// Aidin Gripper SDK - Modbus register map (DH-Robotics RTU compatible)
// Mirrored from firmware: Aidin_gripper_functions/gripper/Inc/aidin_modbus.h
//                        Aidin_gripper_functions/modbus/include/mbtask.h
#pragma once

#include <cstdint>

namespace aidin::reg {

// ---------- Action Request (master -> slave, holding registers) ----------
inline constexpr uint16_t ACTION    = 0x0100;  // rACT|rHOM|rGTO|rATR|rADR
inline constexpr uint16_t SPEED     = 0x0101;  // rSP  0..255
inline constexpr uint16_t FORCE     = 0x0102;  // rFR  0..255
inline constexpr uint16_t POSITION  = 0x0103;  // rPR  0=open .. 255=close

// Action register bit masks
inline constexpr uint16_t RACT = 1u << 0;  // activation request
inline constexpr uint16_t RHOM = 1u << 1;  // homing (rising edge)
inline constexpr uint16_t RGTO = 1u << 3;  // go-to position
inline constexpr uint16_t RATR = 1u << 4;  // auto-release (emergency)
inline constexpr uint16_t RADR = 1u << 5;  // auto-release dir: 0=open, 1=close

// ---------- Gripper Status (slave -> master, holding registers) ----------
inline constexpr uint16_t STATUS      = 0x0200;  // gACT|gHOM|gGTO|gSTA|gOBJ
inline constexpr uint16_t FAULT       = 0x0201;  // gFLT
inline constexpr uint16_t POS_ECHO    = 0x0202;  // gPR (echo of rPR)
inline constexpr uint16_t POS_ACTUAL  = 0x0203;  // gPO 0=open .. 255=close
inline constexpr uint16_t CUR_ACTUAL  = 0x0204;  // gCU 0..255
inline constexpr uint16_t SPD_ACTUAL  = 0x0205;  // gSP 0..255
inline constexpr uint16_t VOLTAGE     = 0x0206;  // gV  [0.1 V units]
inline constexpr uint16_t FAULT_LATCH = 0x0207;  // gFLTO

// Status register bit masks
inline constexpr uint16_t GACT      = 1u << 0;
inline constexpr uint16_t GHOM      = 1u << 1;
inline constexpr uint16_t GGTO      = 1u << 3;
inline constexpr uint16_t GSTA_MASK = 0x3u << 4;
inline constexpr uint16_t GSTA_RESET  = 0x0u << 4;
inline constexpr uint16_t GSTA_INIT   = 0x1u << 4;
inline constexpr uint16_t GSTA_ACTIVE = 0x3u << 4;
inline constexpr uint16_t GOBJ_MASK   = 0x3u << 6;
inline constexpr uint16_t GOBJ_MOVING = 0x0u << 6;
inline constexpr uint16_t GOBJ_OPEN   = 0x1u << 6;
inline constexpr uint16_t GOBJ_CLOSE  = 0x2u << 6;
inline constexpr uint16_t GOBJ_TARGET = 0x3u << 6;

// ---------- Device configuration (factory / installer) ----------
inline constexpr uint16_t CFG_MB_ADDR    = 0x0182;  // slave address 1..247
inline constexpr uint16_t CFG_MB_BAUD_LO = 0x0183;  // baud [15:0]
inline constexpr uint16_t CFG_MB_BAUD_HI = 0x0184;  // baud [31:16]
inline constexpr uint16_t CFG_CAN_ID     = 0x0185;
inline constexpr uint16_t CFG_CAN_RATE   = 0x0186;
inline constexpr uint16_t CFG_DEV_TYPE   = 0x0187;  // 101=Aidin gripper, 102=Apicoo, 103=AFT200, 104=AFT150
inline constexpr uint16_t CFG_SERIAL_LO  = 0x0188;
inline constexpr uint16_t CFG_SERIAL_HI  = 0x0189;

// Baudrate code (CFG_MB_BAUD_LO/HI encodes raw bps, not the code below; the
// code is only used by some legacy firmware. Prefer writing the raw bps value.)
//   0=9600  1=19200  2=38400  3=57600  4=115200  5=230400

// Developer command registers (factory use only)
inline constexpr uint16_t DEV_CMD    = 0x0180;
inline constexpr uint16_t DEV_STATUS = 0x0181;

// DEV_CMD codes (docs/protocol/protocol.md §3 — full list lives there)
inline constexpr uint16_t DEV_CMD_FAULT_CLEAR = 0x07;

// DEV_STATUS codes
inline constexpr uint16_t DEV_STATUS_IDLE    = 0x00;
inline constexpr uint16_t DEV_STATUS_RUNNING = 0x01;
inline constexpr uint16_t DEV_STATUS_OK      = 0x02;
inline constexpr uint16_t DEV_STATUS_ERROR   = 0x03;

} // namespace aidin::reg
