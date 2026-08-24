"""Example 5: Inspect faults and recover with emergency release.

Covers:
  - `fault` (gFLT, transient) vs `latched_fault` (gFLTO, sticky) fields
  - `emergency_release()` to free a stuck object
  - Recovery: emergency_release() drops rACT, so call `activate()` again
    afterwards to resume normal move_to() operation

Usage:
    python 05_fault_and_emergency_release.py /dev/ttyUSB0 [open|close]
    python 05_fault_and_emergency_release.py COM3 close
"""
import sys

from aidin_gripper import Gripper


def main() -> int:
    default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    port = sys.argv[1] if len(sys.argv) > 1 else default_port
    direction = sys.argv[2] if len(sys.argv) > 2 else "open"
    if direction not in ("open", "close"):
        print("direction must be 'open' or 'close'", file=sys.stderr)
        return 1

    try:
        with Gripper() as g:
            g.connect(port)

            s = g.read_state()
            print(f"Before: {s}")
            if s.fault:
                print(f"  active fault code: {s.fault}")
            if s.latched_fault:
                print(f"  latched fault code: {s.latched_fault} "
                      "(clearing it needs the factory DEV_CMD_FAULT_CLEAR "
                      "command - see aidin_gripper.registers)")

            print(f"Emergency release ({direction}) ...")
            g.emergency_release(close_direction=(direction == "close"))
            print(f"  -> {g.read_state()}")

            # emergency_release() writes rATR (and drops rACT), so the
            # gripper won't accept move_to() again until we re-activate.
            print("Re-activating to clear the release latch ...")
            g.activate()
            print(f"  -> {g.read_state()}")

            print("Done.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
