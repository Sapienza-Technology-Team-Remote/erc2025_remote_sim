#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, EnvironmentVariable
from launch_ros.actions import SetUseSimTime
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import ReplaceString
from launch.conditions import IfCondition


def launch_setup(context):
    gz_gui = LaunchConfiguration("gz_gui").perform(context)
    gz_headless_mode = LaunchConfiguration("gz_headless_mode").perform(context)
    gz_log_level = LaunchConfiguration("gz_log_level").perform(context)
    gz_world = LaunchConfiguration("gz_world").perform(context)

    gz_args = f"-r -v {gz_log_level} {gz_world}"
    if eval(gz_headless_mode):
        gz_args = "--headless-rendering -s " + gz_args
    if gz_gui:
        gz_args = f"--gui-config {gz_gui} " + gz_args

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
        ),
        launch_arguments={"gz_args": gz_args, 'on_exit_shutdown': 'true'}.items()
    )

    return [gz_sim]


def generate_launch_description():

    # Dichiarare gli argomenti per la configurazione di Gazebo
    declare_gz_gui = DeclareLaunchArgument(
        "gz_gui",
        default_value=PathJoinSubstitution(
            [FindPackageShare("erc2025_remote_sim"), "config", "teleop.config"]
        ),
        description="Run simulation with specific GUI layout.",
    )

    declare_gz_headless_mode = DeclareLaunchArgument(
        "gz_headless_mode",
        default_value="False",
        description="Run the simulation in headless mode.",
        choices=["True", "False"],
    )

    declare_gz_log_level = DeclareLaunchArgument(
        "gz_log_level",
        default_value="2",
        description="Adjust the level of console output.",
        choices=["0", "1", "2", "3", "4"],
    )

    declare_gz_world_arg = DeclareLaunchArgument(
        "gz_world",
        default_value=PathJoinSubstitution(
            [FindPackageShare("erc2025_remote_sim"), "worlds", "marsyard2024.world"]
        ),
        description="Absolute path to SDF world file.",
    )

    # Dichiarare gli argomenti per la simulazione del robot e RViz
    declare_namespace_arg = DeclareLaunchArgument(
        "namespace",
        default_value=EnvironmentVariable("ROBOT_NAMESPACE", default_value=""),
        description="Add namespace to all launched nodes.",
    )

    declare_robot_model_arg = DeclareLaunchArgument(
        "robot_model",
        default_value=EnvironmentVariable(name="ROBOT_MODEL_NAME", default_value="panther"),
        description="Specify robot model.",
        choices=["lynx", "panther"],
    )

    declare_log_level_arg = DeclareLaunchArgument(
        "log_level",
        default_value="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"],
        description="Logging level",
    )

    declare_use_rviz_arg = DeclareLaunchArgument(
        "use_rviz",
        default_value="False",
        description="Run RViz simultaneously.",
        choices=["True", "false", "False", "true"],
    )


    # Lanciare RViz se specificato
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("husarion_ugv_description"), "launch", "rviz.launch.py"])
        ),
        condition=IfCondition(LaunchConfiguration("use_rviz")),
        launch_arguments={
            "use_rviz": LaunchConfiguration("use_rviz")
        }.items(), 
    )

    # Lanciare il robot
    simulate_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare("husarion_ugv_gazebo"), "launch", "simulate_robot.launch.py"])
        ),
        launch_arguments={
            "log_level": LaunchConfiguration("log_level")
        }.items(), 
    )

    # Launch setup function to handle the gazebo simulation details
    launch_simulation = OpaqueFunction(function=launch_setup)

    actions = [
        declare_gz_gui,
        declare_gz_headless_mode,
        declare_gz_log_level,
        declare_gz_world_arg,
        declare_namespace_arg,
        declare_robot_model_arg,
        declare_log_level_arg,
        declare_use_rviz_arg,
        SetUseSimTime(True), 
        rviz_launch,
        simulate_robot,
        launch_simulation, 
    ]

    return LaunchDescription(actions)
