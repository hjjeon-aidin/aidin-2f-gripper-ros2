// Aidin Gripper SDK - implementation over the self-contained ModbusRtu
// transport (no external Modbus library).
#include "aidin/gripper.hpp"
#include "aidin/modbus_rtu.hpp"
#include "aidin/registers.hpp"

#include <array>
#include <thread>

namespace aidin {

namespace {

constexpr auto kPollInterval = std::chrono::milliseconds(20);
// rHOM/rATR are rising-edge triggered and rGTO re-execution needs a 0->1
// pulse (protocol.md §1, v1.9.1) — hold each edge for this long.
constexpr auto kEdgePulse = std::chrono::milliseconds(20);

std::string hexAddr(uint16_t addr) {
    static const char* digits = "0123456789ABCDEF";
    std::string s = "0x";
    for (int shift = 12; shift >= 0; shift -= 4) {
        s += digits[(addr >> shift) & 0xF];
    }
    return s;
}

} // namespace

struct Gripper::Impl {
    ModbusRtu bus;
    uint8_t   slaveId      = 1;
    uint16_t  lastAction   = 0;   // last ACTION written (rGTO pulse decision)
    int       lastPosition = -1;  // last rPR written, -1 = none yet

    void write1(uint16_t addr, uint16_t value) {
        if (!bus.isOpen()) throw GripperError("not connected");
        if (!bus.writeSingle(slaveId, addr, value)) {
            throw GripperError("write " + hexAddr(addr) + " failed: " + bus.lastError());
        }
        if (addr == reg::ACTION)   lastAction   = value;
        if (addr == reg::POSITION) lastPosition = static_cast<int>(value & 0xFF);
    }

    uint16_t read1(uint16_t addr) {
        if (!bus.isOpen()) throw GripperError("not connected");
        uint16_t v = 0;
        if (!bus.readHolding(slaveId, addr, 1, &v)) {
            throw GripperError("read " + hexAddr(addr) + " failed: " + bus.lastError());
        }
        return v;
    }

    void readBlock(uint16_t addr, uint16_t count, uint16_t* out) {
        if (!bus.isOpen()) throw GripperError("not connected");
        if (!bus.readHolding(slaveId, addr, count, out)) {
            throw GripperError("read block " + hexAddr(addr) + " failed: " + bus.lastError());
        }
    }
};

Gripper::Gripper() : p_(std::make_unique<Impl>()) {}
Gripper::~Gripper() = default;
Gripper::Gripper(Gripper&&) noexcept = default;
Gripper& Gripper::operator=(Gripper&&) noexcept = default;

void Gripper::connect(const std::string& port,
                      int  baudrate,
                      char parity,
                      int  slaveId)
{
    if (slaveId < 1 || slaveId > 247) {
        throw GripperError("slave id out of range (1..247)");
    }
    if (!p_->bus.open(port, baudrate, parity)) {
        throw GripperError("connect failed: " + p_->bus.lastError());
    }
    p_->slaveId      = static_cast<uint8_t>(slaveId);
    p_->lastAction   = 0;
    p_->lastPosition = -1;
}

void Gripper::disconnect() noexcept { p_->bus.close(); }
bool Gripper::isConnected() const noexcept { return p_->bus.isOpen(); }

void Gripper::setResponseTimeout(std::chrono::milliseconds t) {
    p_->bus.setResponseTimeout(t);
}

void Gripper::activate(std::chrono::milliseconds timeout) {
    p_->write1(reg::ACTION, reg::RACT);
    const auto deadline = std::chrono::steady_clock::now() + timeout;
    while (std::chrono::steady_clock::now() < deadline) {
        if (readState().stage == GripperStage::Active) return;
        std::this_thread::sleep_for(kPollInterval);
    }
    throw GripperError("activate timeout (gSTA never reached Active)");
}

void Gripper::deactivate() {
    p_->write1(reg::ACTION, 0);
}

void Gripper::stop() {
    // rGTO=0 stops an in-flight motion; the position regulator keeps holding.
    p_->write1(reg::ACTION, reg::RACT);
}

void Gripper::home(std::chrono::milliseconds timeout) {
    // Activation must be set; firmware homes on rising edge of rHOM.
    p_->write1(reg::ACTION, reg::RACT);            // ensure rHOM is low
    std::this_thread::sleep_for(kEdgePulse);
    p_->write1(reg::ACTION, reg::RACT | reg::RHOM);

    // Let firmware observe the rising edge and clear gHOM before we poll —
    // otherwise we might briefly see the previous-cycle gHOM=1 and return early.
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    const auto deadline = std::chrono::steady_clock::now() + timeout;
    while (std::chrono::steady_clock::now() < deadline) {
        const auto s = readState();
        if (s.fault) {
            throw GripperError("homing fault code=" + std::to_string(s.fault));
        }
        if (s.homed) {
            // clear rHOM so next call sees a fresh rising edge
            p_->write1(reg::ACTION, reg::RACT);
            return;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    p_->write1(reg::ACTION, reg::RACT);            // don't leave rHOM latched
    throw GripperError("home timeout");
}

void Gripper::moveTo(uint8_t position,
                     uint8_t speed,
                     uint8_t force,
                     bool    blocking,
                     std::chrono::milliseconds timeout)
{
    p_->write1(reg::SPEED, speed);
    p_->write1(reg::FORCE, force);

    // Firmware executes goto only on an rGTO rising edge OR an rPR change
    // (protocol.md §1, v1.9.1). Re-issuing the same position while rGTO is
    // already high would be silently ignored — pulse rGTO 0->1 instead.
    const bool samePos = (p_->lastPosition == static_cast<int>(position));
    if (samePos && (p_->lastAction & reg::RGTO)) {
        p_->write1(reg::ACTION, reg::RACT);
        std::this_thread::sleep_for(kEdgePulse);
    } else if (!samePos) {
        p_->write1(reg::POSITION, position);       // rPR first, ACTION last
    }
    p_->write1(reg::ACTION, reg::RACT | reg::RGTO);

    if (!blocking) return;

    const auto deadline = std::chrono::steady_clock::now() + timeout;
    // Give the gripper a moment to leave the previous AtTarget state.
    std::this_thread::sleep_for(std::chrono::milliseconds(30));
    while (std::chrono::steady_clock::now() < deadline) {
        const auto s = readState();
        if (s.fault) {
            throw GripperError("move fault code=" + std::to_string(s.fault));
        }
        if (s.object != ObjectState::Moving) return;
        std::this_thread::sleep_for(kPollInterval);
    }
    throw GripperError("moveTo timeout");
}

void Gripper::emergencyRelease(bool closeDirection) {
    // rATR is a rising edge processed only while rACT=1 (firmware ignores all
    // commands with rACT low) — keep rACT set and pulse rATR. Writing rATR
    // alone would just deactivate the motor without releasing, and would
    // poison the firmware's edge tracking for the next attempt.
    uint16_t bits = reg::RACT | reg::RATR;
    if (closeDirection) bits |= reg::RADR;
    p_->write1(reg::ACTION, bits);
    std::this_thread::sleep_for(kEdgePulse);
    p_->write1(reg::ACTION, reg::RACT);
}

GripperState Gripper::readState() {
    // Read the full status block (0x0200 .. 0x0207) in one transaction.
    std::array<uint16_t, 8> buf{};
    p_->readBlock(reg::STATUS, static_cast<uint16_t>(buf.size()), buf.data());

    GripperState s;
    const uint16_t st = buf[0];
    s.activated  = (st & reg::GACT) != 0;
    s.homed      = (st & reg::GHOM) != 0;
    s.goToActive = (st & reg::GGTO) != 0;

    switch (st & reg::GSTA_MASK) {
        case reg::GSTA_RESET:  s.stage = GripperStage::Reset;      break;
        case reg::GSTA_INIT:   s.stage = GripperStage::Activating; break;
        case reg::GSTA_ACTIVE: s.stage = GripperStage::Active;     break;
        default:               s.stage = GripperStage::Reset;      break;
    }
    switch (st & reg::GOBJ_MASK) {
        case reg::GOBJ_MOVING: s.object = ObjectState::Moving;        break;
        case reg::GOBJ_OPEN:   s.object = ObjectState::OpenContact;   break;
        case reg::GOBJ_CLOSE:  s.object = ObjectState::ClosedContact; break;
        case reg::GOBJ_TARGET: s.object = ObjectState::AtTarget;      break;
    }

    s.fault        = static_cast<uint8_t>(buf[1] & 0xFF);
    s.positionEcho = static_cast<uint8_t>(buf[2] & 0xFF);
    s.position     = static_cast<uint8_t>(buf[3] & 0xFF);
    s.current      = static_cast<uint8_t>(buf[4] & 0xFF);
    s.speed        = static_cast<uint8_t>(buf[5] & 0xFF);
    s.voltage      = static_cast<float>(buf[6]) * 0.1f;
    s.latchedFault = static_cast<uint8_t>(buf[7] & 0xFF);
    return s;
}

bool Gripper::isAtTarget() { return readState().object == ObjectState::AtTarget; }
bool Gripper::hasFault()   { return readState().fault != 0; }

uint16_t Gripper::readRegister(uint16_t pduAddr) {
    return p_->read1(pduAddr);
}
void Gripper::writeRegister(uint16_t pduAddr, uint16_t value) {
    p_->write1(pduAddr, value);
}

} // namespace aidin
