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
from launch_ros.actions import Node, SetUseSimTime, SetParameter
from launch_ros.substitutions import FindPackageShare
from launch.actions import TimerAction
import yaml
import os
from launch.actions import OpaqueFunction

depth_topic = '/front_cam/zed_node/depth'
rgb_topic = '/front_cam/zed_node/rgb/image_rect_color'
camera_info_topic = '/front_cam/zed_node/rgb/camera_info'
left_image_topic = rgb_topic
left_camera_info_topic = camera_info_topic

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    declare_use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value=use_sim_time,
        description="Use simulation clock if true",
        choices=["true", "false"],
    )


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
        default_value="false",
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

    declare_start_location_arg = DeclareLaunchArgument(
        "start_location",
       default_value="1",
        description="Start location ID (1, 2, 3, 4)",
       choices=["1", "2", "3", "4"],
    )
    
    start_location = LaunchConfiguration("start_location")
    package_share_directory = FindPackageShare("erc2025_remote_sim").find("erc2025_remote_sim")
    locations_file_path = os.path.join(package_share_directory, "config", "start_locations.yaml")
    with open(locations_file_path, 'r') as file:
        locations = yaml.safe_load(file)["locations"]
    location_params = locations.get(start_location, locations[1])
    
    x, y, z = location_params["position"]
    R, P, Y = location_params["orientation"]

    declare_x_arg = DeclareLaunchArgument("x", default_value=str(x), description="X position")
    declare_y_arg = DeclareLaunchArgument("y", default_value=str(y), description="Y position")
    declare_z_arg = DeclareLaunchArgument("z", default_value=str(z), description="Z position")
    declare_roll_arg = DeclareLaunchArgument("roll", default_value=str(R), description="Roll orientation")
    declare_pitch_arg = DeclareLaunchArgument("pitch", default_value=str(P), description="Pitch orientation")
    declare_yaw_arg = DeclareLaunchArgument("yaw", default_value=str(Y), description="Yaw orientation")

    declare_ekf= DeclareLaunchArgument("use_ekf", default_value="false", description="Disable_ekf")

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

    #* GZ bridge is called automatically so this one is not needed. If used there are some conflicts
    #if uncommented there are two gz_bridge nodes that cause problems
    # gz_bridge_config = PathJoinSubstitution(
    #     [FindPackageShare("husarion_ugv_gazebo"), "config", "gz_bridge.yaml"]
    # )
    # gz_bridge = Node(
    #     package="ros_gz_bridge",
    #     executable="parameter_bridge",
    #     name="gz_bridge",
    #     parameters=[{"config_file": gz_bridge_config}],
    # )

    simulate_robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("husarion_ugv_gazebo"), "launch", "simulate_robot.launch.py"
            ])
        ),
        launch_arguments={
            "log_level": LaunchConfiguration("log_level"),
            "components_config_path": LaunchConfiguration("components_config_path"),
        }.items(),
    )

    # 5 seconds delay 
    simulate_robot = TimerAction(
        period=5.0,
        actions=[simulate_robot_launch],
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

    gz_image_bridge_node = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=[
            "/front_cam/zed_node/rgb/image_rect_color",
        ],
        output="screen",
        parameters=[
            {'use_sim_time': True},
            {'front_cam.zed_node.rgb.image_rect_color.compressed.jpeg_quality': 75},
        ],
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )



    #Need this node otherwise pointcloud generated by Gazebo is rotated. 
    create_pointcloud_node = Node(
            package='depth_image_proc',
            executable='point_cloud_xyzrgb_node',
            name='point_cloud_xyz_node',
            remappings=[
                ('rgb/camera_info', left_camera_info_topic),
                ('rgb/image_rect_color', rgb_topic),
                ('depth_registered/image_rect', depth_topic),
                ('points', "/pointcloud"),
            ],
            parameters=[
                #is this needed?
                {"qos_overrides./parameter_events.publisher.reliability", "reliable"},
            ],
        )
    

    def fix_velodyne_tf(context, *args, **kwargs):
        namespace = LaunchConfiguration("namespace").perform(context)
        if namespace.startswith("/"):
            namespace = namespace[1:]

        parent_frame = f"{namespace}/lidar_velodyne_puck_link"
        child_frame = f"{namespace}/base_link/lidar_velodyne_puck_sensor"  

        return [
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="fix_velodyne_tf",
                output="screen",
                arguments=["0", "0", "0", "0", "0", "0", parent_frame, child_frame],
                parameters=[{"use_sim_time": True}],
                namespace=namespace,
            )
        ]


    actions = [
        SetParameter(name='use_sim_time', value=use_sim_time),
        declare_use_sim_time_arg,
        declare_gz_gui,
        declare_log_level_arg,
        declare_namespace_arg,
        declare_use_rviz_arg,
        declare_components_config_path_arg,
        declare_start_location_arg,
        declare_x_arg,
        declare_y_arg,
        declare_z_arg,
        declare_roll_arg,
        declare_pitch_arg,
        declare_yaw_arg,
        declare_ekf,
        gz_sim,
        #clock_bridge,
        rviz_launch,
        gz_image_bridge_node,
        simulate_robot,
        #create_pointcloud_node
        OpaqueFunction(function=fix_velodyne_tf),

    ]

    return LaunchDescription(actions)
