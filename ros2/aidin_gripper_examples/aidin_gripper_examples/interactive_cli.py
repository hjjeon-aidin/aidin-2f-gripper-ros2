"""Tiny interactive REPL for poking the AIDIN gripper driver.

Commands:
    a       activate
    d       deactivate
    h       home
    m <p>   move to position 0..255  (e.g. 'm 200')
    e       emergency release (open)
    ec      emergency release (close)
    q       quit
"""
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from aidin_gripper_msgs.srv import MoveTo, EmergencyRelease


class InteractiveCli(Node):
    NS = "/aidin_gripper_driver"

    def __init__(self):
        super().__init__("aidin_interactive_cli")
        self.cli_act  = self.create_client(Trigger, f"{self.NS}/activate")
        self.cli_dea  = self.create_client(Trigger, f"{self.NS}/deactivate")
        self.cli_hom  = self.create_client(Trigger, f"{self.NS}/home")
        self.cli_mov  = self.create_client(MoveTo,  f"{self.NS}/move_to")
        self.cli_rel  = self.create_client(EmergencyRelease,
                                           f"{self.NS}/emergency_release")
        for c in (self.cli_act, self.cli_dea, self.cli_hom,
                  self.cli_mov, self.cli_rel):
            c.wait_for_service(timeout_sec=3.0)

    def _spin(self, fut, t=10.0):
        rclpy.spin_until_future_complete(self, fut, timeout_sec=t)
        return fut.result()

    def call_trigger(self, cli):
        r = self._spin(cli.call_async(Trigger.Request()))
        print(f"  -> {r.message if r else 'no response'}")

    def call_move(self, pos):
        req = MoveTo.Request()
        req.position = pos
        req.speed    = 200
        req.force    = 128
        req.blocking = True
        req.timeout_sec = 5.0
        r = self._spin(self.cli_mov.call_async(req))
        print(f"  -> pos={r.final_position} obj={r.final_object_state}")

    def call_release(self, close_dir):
        req = EmergencyRelease.Request()
        req.close_direction = close_dir
        r = self._spin(self.cli_rel.call_async(req))
        print(f"  -> {r.message if r else 'no response'}")


def main():
    rclpy.init()
    n = InteractiveCli()
    print(__doc__)
    try:
        while True:
            try:
                line = input("aidin> ").strip().split()
            except EOFError:
                break
            if not line: continue
            cmd, *args = line
            if   cmd == "q": break
            elif cmd == "a": n.call_trigger(n.cli_act)
            elif cmd == "d": n.call_trigger(n.cli_dea)
            elif cmd == "h": n.call_trigger(n.cli_hom)
            elif cmd == "m" and args: n.call_move(int(args[0]) & 0xFF)
            elif cmd == "e":  n.call_release(False)
            elif cmd == "ec": n.call_release(True)
            else: print("?  type one of: a d h m <p> e ec q")
    finally:
        rclpy.shutdown()
