"""Example 6: Full quickstart - connect, activate, home, move, report status.

The complete happy-path sequence from a cold power-on, with progress
messages at each step. Run this first on a new gripper to confirm the
serial link and the mechanics both work end to end.

Usage:
    python 06_full_quickstart_demo.py /dev/ttyUSB0
    python 06_full_quickstart_demo.py COM3
"""
import sys

from aidin_gripper import Gripper


def main() -> int:
    default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    port = sys.argv[1] if len(sys.argv) > 1 else default_port

    try:
        with Gripper() as g:
            print(f"1. Connecting to {port} ...")
            g.connect(port)

            print("2. Activating ...")
            g.activate()

            print("3. Homing (fingers seek a hard stop - keep hands clear) ...")
            g.home()

            print("4. Closing ...")
            g.move_to(255, speed=200, force=128, blocking=True)
            print(f"   -> {g.read_state()}")

            print("5. Opening ...")
            g.move_to(0, speed=200, force=128, blocking=True)
            print(f"   -> {g.read_state()}")

            print("6. Final status:")
            print(f"   {g.read_state()}")

            print("Quickstart complete.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
