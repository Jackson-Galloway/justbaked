#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, LogInfo
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Launch arguments to control components
    launch_robot_description = LaunchConfiguration('launch_robot_description')
    launch_lidar = LaunchConfiguration('launch_lidar')
    launch_mov = LaunchConfiguration('launch_mov')
    launch_temp_sens = LaunchConfiguration('launch_temp_sens')
    launch_slam = LaunchConfiguration('launch_slam')
    launch_nav2 = LaunchConfiguration('launch_nav2')
    launch_rviz = LaunchConfiguration('launch_rviz')
    waypoints_file = LaunchConfiguration('waypoints_file', default='round1.yaml')

    # Get path to startup.launch.py
    startup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory("robot_bringup"),
            "launch",
            "startup.launch.py"
        )),
        launch_arguments={
            'launch_robot_description': launch_robot_description,
            'launch_lidar': launch_lidar,
            'launch_mov': launch_mov,
            'launch_temp_sens': launch_temp_sens,
            'launch_slam': launch_slam,
            'launch_nav2': launch_nav2,
            'launch_rviz': launch_rviz,
        }.items()
    )

    # Launch the C++ waypoint navigation node (delayed to ensure Nav2 is ready)
    waypoint_nav_node = TimerAction(
        period=15.0,  # delay to allow Nav2 to fully start
        actions=[ 
            LogInfo(msg="Launching waypoint_nav_cpp node..."),
            Node(
                package="robot_bringup",
                executable="waypoint_nav_cpp",
                name="waypoint_nav_cpp_node",
                output="screen",
                parameters=[{'waypoints_file': waypoints_file}]
            )
        ]
    )

    # Launch the C++ waypoint navigation node (delayed to ensure Nav2 is ready)
    jitter_node = TimerAction(
        period=35.0,  # delay to allow Nav2 to fully start
        actions=[
            LogInfo(msg="Launching waypoint_nav_cpp node..."),
            Node(
                package="robot_bringup",
                executable="cat_servo_gpiofire.py",
                name="jitter_node",
                output="screen",
                parameters=[{'waypoints_file': waypoints_file}]
            )
        ]
    )


    return LaunchDescription([
        DeclareLaunchArgument(
            'launch_robot_description',
            default_value='true',
            description='Launch robot description'
        ),
        DeclareLaunchArgument(
            'launch_lidar',
            default_value='true',
            description='Launch lidar sensor'
        ),
        DeclareLaunchArgument(
            'launch_mov',
            default_value='true',
            description='Launch tank drive control'
        ),
        DeclareLaunchArgument(
            'launch_temp_sens',
            default_value='false',
            description='Launch temperature sensor node'
        ),
        DeclareLaunchArgument(
            'launch_slam',
            default_value='true',
            description='Launch SLAM Toolbox'
        ),
        DeclareLaunchArgument(
            'launch_nav2',
            default_value='true',
            description='Launch Navigation2'
        ),
        DeclareLaunchArgument(
            'launch_rviz',
            default_value='false',
            description='Launch RViz2'
        ),
        DeclareLaunchArgument(
            'waypoints_file',
            default_value='round1.yaml',
            description='Waypoints file to use (round1.yaml, round2.yaml, round3.yaml)'
        ),
        # Launch core system
        startup_launch,

        # Launch the mission logic
        waypoint_nav_node,

        jitter_node,
     ])

