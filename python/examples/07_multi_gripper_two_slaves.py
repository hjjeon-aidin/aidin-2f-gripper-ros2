"""Example 7: Two grippers on one RS485 bus, two slave IDs.

Both devices must already have distinct Modbus slave addresses (see
"Multiple grippers on one bus" in README.md - write registers.CFG_MB_ADDR
once per device, one at a time, before wiring them together; two
grippers left at the factory default of 1 would both answer at once).

Once wired onto the same bus, just connect() two Gripper instances to
the same port with different slave_id values - the second connect()
transparently reuses the first one's already-open serial connection
instead of trying to open the port again.

Usage:
    python 07_multi_gripper_two_slaves.py /dev/ttyUSB0 [id_a] [id_b]
    python 07_multi_gripper_two_slaves.py COM3 1 2
"""
import sys

from aidin_gripper import Gripper, GripperStage


def main() -> int:
    default_port = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    port = sys.argv[1] if len(sys.argv) > 1 else default_port
    id_a = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    id_b = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    try:
        with Gripper() as a, Gripper() as b:
            print(f"Connecting slave {id_a} on {port} ...")
            a.connect(port, slave_id=id_a)

            print(f"Connecting slave {id_b} on {port} (shares the same link) ...")
            b.connect(port, slave_id=id_b)

            for g in (a, b):
                if g.read_state().stage != GripperStage.ACTIVE:
                    print(f"[id={g.slave_id}] Activating ...")
                    g.activate()

            print(f"[id={a.slave_id}] {a.read_state()}")
            print(f"[id={b.slave_id}] {b.read_state()}")

            print("Done.")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
