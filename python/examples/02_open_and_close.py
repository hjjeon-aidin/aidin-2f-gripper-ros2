"""Example 2: Open and close the gripper once.

Activates/homes first if needed, then does a single close move followed
by a single open move. For a repeated cyclic test see 03_open_close_loop.py.

Usage:
    python 02_open_and_close.py /dev/ttyUSB0
    python 02_open_and_close.py COM3
"""
import sys

from aidin_gripper import Gripper, GripperStage


def main() -> int:
    default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    port = sys.argv[1] if len(sys.argv) > 1 else default_port

    try:
        with Gripper() as g:
            g.connect(port)

            if g.read_state().stage != GripperStage.ACTIVE:
                print("Activating ...")
                g.activate()
            if not g.read_state().homed:
                print("Homing ...")
                g.home()

            print("Closing ...")
            g.move_to(255, speed=200, force=128, blocking=True)
            print(f"  -> {g.read_state()}")

            print("Opening ...")
            g.move_to(0, speed=200, force=128, blocking=True)
            print(f"  -> {g.read_state()}")

            print("Done.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
