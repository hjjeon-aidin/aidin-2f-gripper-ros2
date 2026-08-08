"""Example 1: Activate and home the AIDIN gripper.

Usage:
    python 01_activate_and_home.py /dev/ttyUSB0      (Linux)
    python 01_activate_and_home.py COM3              (Windows)
"""
import sys

from aidin_gripper import Gripper


def main() -> int:
    default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    port = sys.argv[1] if len(sys.argv) > 1 else default_port

    try:
        with Gripper() as g:
            print(f"Connecting to {port} ...")
            g.connect(port)                         # 115200 8N1, slave 1

            print("Activating ...")
            g.activate()
            print(f"  -> state: {g.read_state()}")

            print("Homing (this may take a few seconds) ...")
            g.home()
            print(f"  -> state: {g.read_state()}")

            print("Done.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
