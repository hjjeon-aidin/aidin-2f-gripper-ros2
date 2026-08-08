"""Repeatedly close/open the gripper via the move_to service."""
import sys
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from aidin_gripper_msgs.srv import MoveTo


class OpenCloseLoop(Node):
    def __init__(self, cycles: int):
        super().__init__("aidin_open_close_loop")
        self.cycles = cycles
        self._call(Trigger, "/aidin_gripper_driver/activate")
        self._call(Trigger, "/aidin_gripper_driver/home")

        for i in range(self.cycles):
            self.get_logger().info(f"Cycle {i+1}/{self.cycles}")
            self._move(255)  # close
            self._move(0)    # open

    def _call(self, srv_type, name):
        cli = self.create_client(srv_type, name)
        if not cli.wait_for_service(timeout_sec=3.0):
            raise RuntimeError(f"Service {name} not available")
        fut = cli.call_async(srv_type.Request())
        rclpy.spin_until_future_complete(self, fut, timeout_sec=20.0)
        r = fut.result()
        if not (r and r.success):
            raise RuntimeError(
                f"{name} failed: {getattr(r, 'message', 'no response')}")

    def _move(self, position: int):
        cli = self.create_client(MoveTo, "/aidin_gripper_driver/move_to")
        cli.wait_for_service(timeout_sec=3.0)
        req = MoveTo.Request()
        req.position    = position
        req.speed       = 200
        req.force       = 128
        req.blocking    = True
        req.timeout_sec = 5.0
        fut = cli.call_async(req)
        rclpy.spin_until_future_complete(self, fut, timeout_sec=10.0)
        r = fut.result()
        self.get_logger().info(
            f"  -> pos={r.final_position} obj_state={r.final_object_state}")


def main():
    rclpy.init()
    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    try:
        OpenCloseLoop(cycles)
    finally:
        rclpy.shutdown()
