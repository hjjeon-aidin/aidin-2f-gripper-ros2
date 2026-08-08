"""High-level Python wrapper for the AIDIN BLDC gripper (Modbus RTU).

Mirrors the C++ SDK API:
    g = Gripper()
    g.connect("/dev/ttyUSB0")
    g.activate()
    g.home()
    g.move_to(255, speed=200, force=128, blocking=True)
"""
from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Optional

from pymodbus.client import ModbusSerialClient

from . import registers as reg
from .types import GripperError, GripperStage, GripperState, ObjectState


_POLL_INTERVAL_S = 0.02
_DEFAULT_TIMEOUT_S = 0.5


class Gripper:
    """Controls one AIDIN BLDC gripper over Modbus RTU."""

    def __init__(self) -> None:
        self._client: Optional[ModbusSerialClient] = None
        self._slave_id: int = 1

    # ---------------------------- Lifecycle ----------------------------
    def connect(
        self,
        port: str,
        baudrate: int = 115200,
        parity: str = "N",
        slave_id: int = 1,
        response_timeout_s: float = _DEFAULT_TIMEOUT_S,
    ) -> None:
        """Open serial port and verify the slave responds.

        port: "/dev/ttyUSB0" on Linux, "COM3" on Windows.
        """
        self.disconnect()

        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity=parity,
            stopbits=1,
            bytesize=8,
            timeout=response_timeout_s,
        )
        if not client.connect():
            raise GripperError(f"Cannot open serial port {port!r}")

        self._client = client
        self._slave_id = slave_id

        # Sanity check: a single read to confirm the slave is alive.
        try:
            self._read_block(reg.STATUS, 1)
        except GripperError:
            self.disconnect()
            raise

    def disconnect(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.connected

    def __enter__(self) -> "Gripper":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    # ---------------------------- Commands ----------------------------
    def activate(self, timeout_s: float = 3.0) -> None:
        """Set rACT=1 and wait until gSTA reports ACTIVE."""
        self._write1(reg.ACTION, reg.RACT)
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.read_state().stage == GripperStage.ACTIVE:
                return
            time.sleep(_POLL_INTERVAL_S)
        raise GripperError("activate timeout (gSTA never reached ACTIVE)")

    def deactivate(self) -> None:
        self._write1(reg.ACTION, 0)

    def home(self, timeout_s: float = 15.0) -> None:
        """Trigger homing and block until gHOM=1.

        The firmware homes on the rising edge of rHOM. We clear rHOM first,
        wait briefly, then assert it.
        """
        self._write1(reg.ACTION, reg.RACT)              # ensure rHOM low
        time.sleep(0.02)
        self._write1(reg.ACTION, reg.RACT | reg.RHOM)    # rising edge
        time.sleep(0.10)                                  # let firmware clear gHOM

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            s = self.read_state()
            if s.fault:
                raise GripperError(f"homing fault code={s.fault}")
            if s.homed:
                self._write1(reg.ACTION, reg.RACT)        # release rHOM
                return
            time.sleep(0.05)
        raise GripperError("home timeout")

    def move_to(
        self,
        position: int,
        speed: int = 128,
        force: int = 128,
        blocking: bool = False,
        timeout_s: float = 5.0,
    ) -> None:
        """Move to absolute position. 0 = fully open, 255 = fully closed.

        speed, force: 0..255.  blocking=True polls until gOBJ != MOVING.
        """
        _u8(position, "position")
        _u8(speed,    "speed")
        _u8(force,    "force")

        self._write1(reg.SPEED,    speed)
        self._write1(reg.FORCE,    force)
        self._write1(reg.POSITION, position)
        self._write1(reg.ACTION,   reg.RACT | reg.RGTO)

        if not blocking:
            return

        time.sleep(0.03)  # let the firmware leave the previous AT_TARGET state
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            s = self.read_state()
            if s.fault:
                raise GripperError(f"move fault code={s.fault}")
            if s.object_state != ObjectState.MOVING:
                return
            time.sleep(_POLL_INTERVAL_S)
        raise GripperError("move_to timeout")

    def emergency_release(self, close_direction: bool = False) -> None:
        bits = reg.RATR | (reg.RADR if close_direction else 0)
        self._write1(reg.ACTION, bits)

    # ---------------------------- Status ----------------------------
    def read_state(self) -> GripperState:
        """Read the full status block (0x0200..0x0207) in one transaction."""
        regs = self._read_block(reg.STATUS, 8)
        st = regs[0]

        stage_bits = st & reg.GSTA_MASK
        stage = {
            reg.GSTA_RESET:  GripperStage.RESET,
            reg.GSTA_INIT:   GripperStage.ACTIVATING,
            reg.GSTA_ACTIVE: GripperStage.ACTIVE,
        }.get(stage_bits, GripperStage.RESET)

        obj_bits = st & reg.GOBJ_MASK
        obj = {
            reg.GOBJ_MOVING: ObjectState.MOVING,
            reg.GOBJ_OPEN:   ObjectState.OPEN_CONTACT,
            reg.GOBJ_CLOSE:  ObjectState.CLOSED_CONTACT,
            reg.GOBJ_TARGET: ObjectState.AT_TARGET,
        }.get(obj_bits, ObjectState.MOVING)

        return GripperState(
            activated     = bool(st & reg.GACT),
            homed         = bool(st & reg.GHOM),
            go_to_active  = bool(st & reg.GGTO),
            stage         = stage,
            object_state  = obj,
            fault         = regs[1] & 0xFF,
            position_echo = regs[2] & 0xFF,
            position      = regs[3] & 0xFF,
            current       = regs[4] & 0xFF,
            speed         = regs[5] & 0xFF,
            voltage       = regs[6] * 0.1,
            latched_fault = regs[7] & 0xFF,
        )

    def is_at_target(self) -> bool:
        return self.read_state().object_state == ObjectState.AT_TARGET

    def has_fault(self) -> bool:
        return self.read_state().fault != 0

    # ---------------------------- Low-level ----------------------------
    def read_register(self, pdu_addr: int) -> int:
        """Read a single holding register at its protocol-level PDU address."""
        return self._read_block(pdu_addr, 1)[0]

    def write_register(self, pdu_addr: int, value: int) -> None:
        self._write1(pdu_addr, value)

    # ---------------------------- internals ----------------------------
    def _require_client(self) -> ModbusSerialClient:
        if self._client is None:
            raise GripperError("not connected")
        return self._client

    def _write1(self, addr: int, value: int) -> None:
        c = self._require_client()
        rr = c.write_register(addr, value & 0xFFFF, slave=self._slave_id)
        if rr.isError():
            raise GripperError(
                f"write_register(0x{addr:04X}, 0x{value:04X}) failed: {rr}")

    def _read_block(self, addr: int, count: int) -> list[int]:
        c = self._require_client()
        rr = c.read_holding_registers(addr, count=count, slave=self._slave_id)
        if rr.isError():
            raise GripperError(
                f"read_holding_registers(0x{addr:04X}, {count}) failed: {rr}")
        return list(rr.registers)


def _u8(v: int, name: str) -> None:
    if not (0 <= v <= 255):
        raise ValueError(f"{name} must be in 0..255, got {v}")
