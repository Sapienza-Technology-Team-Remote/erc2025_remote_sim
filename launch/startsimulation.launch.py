#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node, SetUseSimTime
from launch_ros.substitutions import FindPackageShare
import yaml
import os

def generate_launch_description():

    gz_gui = LaunchConfiguration("gz_gui")
    declare_gz_gui = DeclareLaunchArgument(
        "gz_gui",
        default_value=PathJoinSubstitution(
            [FindPackageShare("erc2025_remote_sim"), "config", "teleop.config"]
        ),
        description="Run simulation with specific GUI layout.",
    )

    declare_log_level_arg = DeclareLaunchArgument(
        "log_level",
        default_value="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"],
        description="Logging level",
    )

    declare_namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Add namespace to all launched nodes.",
    )

    declare_use_rviz_arg = DeclareLaunchArgument(
        "use_rviz",
        default_value="False",
        description="Run RViz simultaneously.",
        choices=["True", "true", "False", "false"],
    )

    declare_components_config_path_arg = DeclareLaunchArgument(
        "components_config_path",
        default_value=PathJoinSubstitution([
            FindPackageShare("erc2025_remote_sim"), "config", "components.yaml"
        ]),
        description="Path to the components configuration file for robot simulation",
    )

    
    #declare_start_location_arg = DeclareLaunchArgument(
    #    "start_location",
    #    default_value="1",
    #    description="Start location ID (1, 2, 3, 4)",
    #    choices=["1", "2", "3", "4"],
    #)

    #start_location = LaunchConfiguration("start_location")
    #package_share_directory = FindPackageShare("erc2025_remote_sim").find("erc2025_remote_sim")
    #locations_file_path = os.path.join(package_share_directory, "config", "start_locations.yaml")
    #with open(locations_file_path, 'r') as file:
    #    locations = yaml.safe_load(file)["locations"]
    #location_params = locations.get(start_location, locations[1])
    #
    #x, y, z = location_params["position"]
    #R, P, Y = location_params["orientation"]

    #declare_x_arg = DeclareLaunchArgument("x", default_value=x, description="X position")
    #declare_y_arg = DeclareLaunchArgument("y", default_value=y, description="Y position")
    #declare_z_arg = DeclareLaunchArgument("z", default_value=z, description="Z position")
    #declare_roll_arg = DeclareLaunchArgument("roll", default_value=R, description="Roll orientation")
    #declare_pitch_arg = DeclareLaunchArgument("pitch", default_value=P, description="Pitch orientation")
    #declare_yaw_arg = DeclareLaunchArgument("yaw", default_value=Y, description="Yaw orientation")

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("erc2025_remote_sim"), "launch", "sim_world.launch.py"]
            )
        ),
        launch_arguments={
            "gz_gui": gz_gui,
            "gz_log_level": "1"
        }.items(),
    )

    gz_bridge_config = PathJoinSubstitution(
        [FindPackageShare("husarion_ugv_gazebo"), "config", "gz_bridge.yaml"]
    )
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        parameters=[{"config_file": gz_bridge_config}],
    )

    simulate_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("husarion_ugv_gazebo"), "launch", "simulate_robot.launch.py"])
        ),
        launch_arguments={
            "log_level": LaunchConfiguration("log_level"),
            "components_config_path": LaunchConfiguration("components_config_path"),
            #"x": LaunchConfiguration("x"),
            #"y": LaunchConfiguration("y"),
            #"z": LaunchConfiguration("z"),
            #"roll": LaunchConfiguration("roll"),
            #"pitch": LaunchConfiguration("pitch"),
            #"yaw": LaunchConfiguration("yaw"),
        }.items(),
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("husarion_ugv_description"), "launch", "rviz.launch.py"])
        ),
        condition=IfCondition(LaunchConfiguration("use_rviz")),
        launch_arguments={
            "use_rviz": LaunchConfiguration("use_rviz")
        }.items(),
    )

    actions = [
        declare_gz_gui,
        declare_log_level_arg,
        declare_namespace_arg,
        declare_use_rviz_arg,
        declare_components_config_path_arg,
        #declare_start_location_arg,
        SetUseSimTime(True),
        gz_sim,
        gz_bridge,
        simulate_robot,
        rviz_launch,
    ]

    return LaunchDescription(actions)
