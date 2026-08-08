"""Modbus register map for the AIDIN BLDC gripper (DH-Robotics RTU compatible).

Mirrors the firmware-side definitions in:
  - Aidin_gripper_functions/gripper/Inc/aidin_modbus.h
  - Aidin_gripper_functions/modbus/include/mbtask.h
"""
from typing import Final

# --------------- Action request (master -> slave) ---------------
ACTION:   Final[int] = 0x0100   # rACT | rHOM | rGTO | rATR | rADR
SPEED:    Final[int] = 0x0101   # rSP  0..255
FORCE:    Final[int] = 0x0102   # rFR  0..255
POSITION: Final[int] = 0x0103   # rPR  0=open, 255=close

# Action register bit masks
RACT: Final[int] = 1 << 0
RHOM: Final[int] = 1 << 1
RGTO: Final[int] = 1 << 3
RATR: Final[int] = 1 << 4
RADR: Final[int] = 1 << 5

# --------------- Gripper status (slave -> master) ---------------
STATUS:      Final[int] = 0x0200
FAULT:       Final[int] = 0x0201
POS_ECHO:    Final[int] = 0x0202
POS_ACTUAL:  Final[int] = 0x0203
CUR_ACTUAL:  Final[int] = 0x0204
SPD_ACTUAL:  Final[int] = 0x0205
VOLTAGE:     Final[int] = 0x0206
FAULT_LATCH: Final[int] = 0x0207

# Status register bit masks
GACT:        Final[int] = 1 << 0
GHOM:        Final[int] = 1 << 1
GGTO:        Final[int] = 1 << 3
GSTA_MASK:   Final[int] = 0x3 << 4
GSTA_RESET:  Final[int] = 0x0 << 4
GSTA_INIT:   Final[int] = 0x1 << 4
GSTA_ACTIVE: Final[int] = 0x3 << 4
GOBJ_MASK:   Final[int] = 0x3 << 6
GOBJ_MOVING: Final[int] = 0x0 << 6
GOBJ_OPEN:   Final[int] = 0x1 << 6
GOBJ_CLOSE:  Final[int] = 0x2 << 6
GOBJ_TARGET: Final[int] = 0x3 << 6

# --------------- Configuration (factory / installer) ---------------
CFG_MB_ADDR:    Final[int] = 0x0182   # slave address 1..247
CFG_MB_BAUD_LO: Final[int] = 0x0183   # baud [15:0]
CFG_MB_BAUD_HI: Final[int] = 0x0184   # baud [31:16]
CFG_CAN_ID:     Final[int] = 0x0185
CFG_CAN_RATE:   Final[int] = 0x0186
CFG_DEV_TYPE:   Final[int] = 0x0187   # 101=Aidin, 102=Apicoo, 103=AFT200, 104=AFT150
CFG_SERIAL_LO:  Final[int] = 0x0188
CFG_SERIAL_HI:  Final[int] = 0x0189

DEV_CMD:    Final[int] = 0x0180
DEV_STATUS: Final[int] = 0x0181
