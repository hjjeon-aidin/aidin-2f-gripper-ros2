// Aidin Gripper SDK - self-contained Modbus RTU master transport.
//
// No external Modbus library: builds the RTU ADU (function code + CRC16)
// itself and drives the serial port directly — termios + poll() on POSIX,
// Win32 COMM API on Windows. Supported function codes: 0x03 (Read Holding),
// 0x06 (Write Single), 0x10 (Write Multiple).
//
// Not thread-safe: callers must serialize transactions (Gripper::Impl and
// the ROS2 driver both do).
#pragma once

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <string>

namespace aidin {

class ModbusRtu {
public:
    ModbusRtu() = default;
    ~ModbusRtu();
    ModbusRtu(const ModbusRtu&)            = delete;
    ModbusRtu& operator=(const ModbusRtu&) = delete;

    // Opens the port in raw 8<parity>1 mode. parity: 'N' / 'E' / 'O'.
    // port: "/dev/ttyUSB0" on Linux, "COM3" / "COM10" on Windows
    // (\\.\ prefix added automatically). Returns false + lastError() on failure.
    bool open(const std::string& port, int baudrate, char parity = 'N');
    void close() noexcept;
    bool isOpen() const noexcept;

    // Per-transaction response deadline (default 500 ms — generous enough
    // for slow USB-RS485 dongles; lower it for high-rate polling).
    void setResponseTimeout(std::chrono::milliseconds t) noexcept { timeout_ = t; }

    // FC03 — read `count` (1..125) holding registers into out[0..count-1].
    bool readHolding(uint8_t slave, uint16_t addr, uint16_t count, uint16_t* out);
    // FC06 — write a single register (response echo verified).
    bool writeSingle(uint8_t slave, uint16_t addr, uint16_t value);
    // FC16 — write `count` (1..123) consecutive registers.
    bool writeMultiple(uint8_t slave, uint16_t addr, const uint16_t* values, uint16_t count);

    const std::string& lastError() const noexcept { return lastError_; }

    // Modbus CRC16 (poly 0xA001); transmitted LSB-first on the wire.
    static uint16_t crc16(const uint8_t* data, size_t len) noexcept;

private:
    using Clock = std::chrono::steady_clock;

    // Sends the request (CRC appended — req buffer needs 2 spare bytes) and
    // reads/validates the response. normalLen = full normal-response ADU
    // length incl. CRC; exception frames (func|0x80, 5 bytes) handled inside.
    bool transact(uint8_t* req, size_t reqLenWoCrc, uint8_t* resp, size_t normalLen);
    bool readExact(uint8_t* buf, size_t len, Clock::time_point deadline);
    bool writeAll(const uint8_t* data, size_t len);
    void flushInput() noexcept;
    void guardInterframe() noexcept;

#if defined(_WIN32)
    void* handle_ = nullptr;   // HANDLE; nullptr = closed (keeps windows.h out of this header)
#else
    int fd_ = -1;
#endif
    std::chrono::milliseconds timeout_{500};
    Clock::time_point lastIo_{};
    std::string lastError_;
};

} // namespace aidin
