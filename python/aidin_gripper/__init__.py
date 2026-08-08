"""AIDIN BLDC Gripper - Python SDK.

>>> from aidin_gripper import Gripper
>>> with Gripper() as g:
...     g.connect("/dev/ttyUSB0")
...     g.activate()
...     g.home()
...     g.move_to(255, speed=200, blocking=True)
"""
from .gripper import Gripper
from .types import GripperError, GripperStage, GripperState, ObjectState
from . import registers

__all__ = [
    "Gripper",
    "GripperError",
    "GripperState",
    "GripperStage",
    "ObjectState",
    "registers",
]

__version__ = "1.0.0"
