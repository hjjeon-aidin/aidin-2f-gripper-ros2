// Aidin Gripper SDK - C++ class wrapper
//
// Talks to AIDIN BLDC firmware (DH-Robotics compatible Modbus RTU) over RS485.
// Default link: 115200 8N1, slave ID 1.
//
// Quick start:
//   aidin::Gripper g;
//   g.connect("/dev/ttyUSB0");          // Windows: "COM3"
//   g.activate();
//   g.home();
//   g.moveTo(255, 200, 128, /*blocking=*/true);
#pragma once

#include "aidin/types.hpp"

#include <chrono>
#include <memory>
#include <stdexcept>
#include <string>

namespace aidin {

class GripperError : public std::runtime_error {
public:
    using std::runtime_error::runtime_error;
};

class Gripper {
public:
    Gripper();
    ~Gripper();
    Gripper(const Gripper&)            = delete;
    Gripper& operator=(const Gripper&) = delete;
    Gripper(Gripper&&) noexcept;
    Gripper& operator=(Gripper&&) noexcept;

    // ---------- Connection ----------
    // port: "/dev/ttyUSB0" on Linux, "COM3" / "COM10" on Windows (auto-prefixed)
    // parity: 'N', 'E', or 'O'.  Default 'N' matches firmware default.
    void connect(const std::string& port,
                 int  baudrate = 115200,
                 char parity   = 'N',
                 int  slaveId  = 1);
    void disconnect() noexcept;
    bool isConnected() const noexcept;
    void setResponseTimeout(std::chrono::milliseconds t);

    // ---------- High-level commands ----------
    // Set rACT=1 and wait until gSTA reports Active (or throw on timeout).
    void activate(std::chrono::milliseconds timeout = std::chrono::seconds(3));
    // Set rACT=0. Does not wait.
    void deactivate();
    // Stop an in-flight motion (rGTO=0). Motor stays activated and holding.
    void stop();
    // Trigger homing (rising edge of rHOM) and block until gHOM=1.
    void home(std::chrono::milliseconds timeout = std::chrono::seconds(15));
    // Move to absolute position. 0=fully open, 255=fully closed.
    //   speed:  0..255   force/current limit: 0..255
    //   blocking=true waits until gOBJ != Moving (target reached or object hit).
    void moveTo(uint8_t position,
                uint8_t speed   = 128,
                uint8_t force   = 128,
                bool    blocking = false,
                std::chrono::milliseconds timeout = std::chrono::seconds(5));
    // Emergency release. dir=false opens, true closes. Sets rATR; user must
    // clear by calling activate() again.
    void emergencyRelease(bool closeDirection = false);

    // ---------- Status ----------
    GripperState readState();
    bool         isAtTarget();
    bool         hasFault();

    // ---------- Low-level escape hatch ----------
    // Direct Modbus register access. pduAddr is the protocol-level address
    // (e.g. 0x0100, 0x0200, 0x0182). Mostly useful for installer / factory
    // tooling that needs to read/write configuration registers.
    uint16_t readRegister(uint16_t pduAddr);
    void     writeRegister(uint16_t pduAddr, uint16_t value);

private:
    struct Impl;
    std::unique_ptr<Impl> p_;
};

} // namespace aidin
