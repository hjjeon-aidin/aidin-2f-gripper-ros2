"""Spawn the AIDIN gripper URDF into Gazebo Sim (ros_gz)."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare("aidin_gripper_description")
    pkg_ros_gz_sim = FindPackageShare("ros_gz_sim")
    default_model = PathJoinSubstitution([pkg, "urdf", "ASSY_URDF.SLDASM3.urdf"])

    robot_description = ParameterValue(
        Command(["cat ", LaunchConfiguration("model")]), value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument(
            "model",
            default_value=default_model,
            description="Path to the gripper URDF file to spawn."),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([pkg_ros_gz_sim, "launch", "gz_sim.launch.py"])),
            launch_arguments={"gz_args": "empty.sdf -r"}.items(),
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[{"robot_description": robot_description}],
        ),
        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=["-topic", "robot_description", "-name", "aidin_gripper"],
            output="screen",
        ),
    ])
