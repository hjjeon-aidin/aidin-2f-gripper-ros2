"""Public types for the AIDIN gripper Python SDK."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class GripperStage(IntEnum):
    RESET      = 0
    ACTIVATING = 1
    ACTIVE     = 3


class ObjectState(IntEnum):
    MOVING         = 0
    OPEN_CONTACT   = 1   # object detected while opening
    CLOSED_CONTACT = 2   # object detected while closing
    AT_TARGET      = 3


@dataclass
class GripperState:
    activated:     bool         = False
    homed:         bool         = False
    go_to_active:  bool         = False
    stage:         GripperStage = GripperStage.RESET
    object_state:  ObjectState  = ObjectState.MOVING
    fault:         int          = 0      # gFLT
    position_echo: int          = 0      # gPR
    position:      int          = 0      # gPO 0..255 (0=open, 255=close)
    current:       int          = 0      # gCU 0..255
    speed:         int          = 0      # gSP 0..255
    voltage:       float        = 0.0    # V (gV * 0.1)
    latched_fault: int          = 0      # gFLTO

    def __str__(self) -> str:
        return (
            f"{{stage={self.stage.name} obj={self.object_state.name} "
            f"pos={self.position} cur={self.current} spd={self.speed} "
            f"V={self.voltage:.1f} flt={self.fault}}}"
        )


class GripperError(RuntimeError):
    """Raised on Modbus failure or command timeout."""
    pass
