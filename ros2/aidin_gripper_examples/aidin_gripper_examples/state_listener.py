"""Subscribe to /aidin_gripper_driver/state and print changes."""
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from aidin_gripper_msgs.msg import GripperState

_OBJECT = {0: "MOVING", 1: "OPEN_CONTACT", 2: "CLOSED_CONTACT", 3: "AT_TARGET"}
_STAGE  = {0: "RESET",  1: "ACTIVATING",   3: "ACTIVE"}


class StateListener(Node):
    def __init__(self):
        super().__init__("aidin_gripper_state_listener")
        self.last = None
        self.create_subscription(
            GripperState,
            "/aidin_gripper_driver/state",
            self.cb,
            qos_profile_sensor_data,
        )
        self.get_logger().info("Listening for /aidin_gripper_driver/state ...")

    def cb(self, msg: GripperState):
        sig = (msg.stage, msg.object_state, msg.position, msg.fault)
        if sig == self.last:
            return
        self.last = sig
        self.get_logger().info(
            f"stage={_STAGE.get(msg.stage,'?')} "
            f"obj={_OBJECT.get(msg.object_state,'?')} "
            f"pos={msg.position} cur={msg.current} V={msg.voltage:.1f} "
            f"flt={msg.fault}")


def main():
    rclpy.init()
    try:
        rclpy.spin(StateListener())
    finally:
        rclpy.shutdown()
