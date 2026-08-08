"""Example 3: Continuously print gripper state changes (100 ms polling).

Usage:
    python 03_status_monitor.py /dev/ttyUSB0
    python 03_status_monitor.py COM3
"""
import signal
import sys
import time

from aidin_gripper import Gripper


_stop = False


def _on_signal(_signum, _frame):
    global _stop
    _stop = True


def main() -> int:
    default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    port = sys.argv[1] if len(sys.argv) > 1 else default_port

    signal.signal(signal.SIGINT, _on_signal)

    try:
        with Gripper() as g:
            g.connect(port)
            print(f"Monitoring {port} (CTRL+C to quit)")

            prev_sig = None
            while not _stop:
                s = g.read_state()
                sig = (s.stage, s.object_state, s.position, s.fault,
                       s.current // 6)            # bucket current to dampen jitter
                if sig != prev_sig:
                    print(s)
                    prev_sig = sig
                time.sleep(0.1)
            print("Stopped.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
