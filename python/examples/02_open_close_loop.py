"""Example 2: Repeatedly open and close the gripper.

Usage:
    python 02_open_close_loop.py /dev/ttyUSB0 [cycles]
    python 02_open_close_loop.py COM3 [cycles]
"""
import signal
import sys

from aidin_gripper import Gripper, GripperStage


_stop = False


def _on_signal(_signum, _frame):
    global _stop
    _stop = True


def main() -> int:
    default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    port   = sys.argv[1] if len(sys.argv) > 1 else default_port
    cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    signal.signal(signal.SIGINT, _on_signal)

    try:
        with Gripper() as g:
            g.connect(port)

            if g.read_state().stage != GripperStage.ACTIVE:
                print("Activating ...")
                g.activate()
            if not g.read_state().homed:
                print("Homing ...")
                g.home()

            for i in range(cycles):
                if _stop:
                    break
                print(f"Cycle {i + 1}/{cycles}")

                print("  close ...")
                g.move_to(255, speed=200, force=128, blocking=True)
                print(f"    {g.read_state()}")

                if _stop:
                    break

                print("  open ...")
                g.move_to(0, speed=200, force=128, blocking=True)
                print(f"    {g.read_state()}")

            print("Interrupted." if _stop else "Done.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
