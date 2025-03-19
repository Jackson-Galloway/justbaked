import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get paths to required launch files
    turtlebot4_description_launch = os.path.join(
        get_package_share_directory("turtlebot4_description"),
        "launch",
        "robot_description.launch.py",  # Ensure this file exists or adjust name
    )

    lidar_launch_file = os.path.join(
        get_package_share_directory("sllidar_ros2"),
        "launch",
        "sllidar_a1_launch.py",
    )
    tank_mov_launch_file = os.path.join(
        get_package_share_directory("turtlebot4_navigation"),
        "launch",
        "tank_mov.launch.py",
    )
    slam_launch_file = os.path.join(
        get_package_share_directory("turtlebot4_navigation"),
        "launch",
        "slam.launch.py",
    )

    nav2_launch_file = os.path.join(
        get_package_share_directory("turtlebot4_navigation"),
        "launch",
        "nav2.launch.py",
    )

    # Robot Description
    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(turtlebot4_description_launch),
        launch_arguments={"model": "standard", "use_sim_time": "false"}.items(),
    )

    # LIDAR Sensor
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch_file)
    )

    # Tank Movement
    tank_mov = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(tank_mov_launch_file)
    )

    # SLAM Toolbox
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_file),
        launch_arguments={
            "use_sim_time": "false",
            "sync": "false",
            "autostart": "true",
            "use_lifecycle_manager": "false",
            "params": os.path.join(
                get_package_share_directory("turtlebot4_navigation"),
                "config",
                "slam.yaml"
            ),
        }.items(),
    )

    # Navigation 2 (Nav2)
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(nav2_launch_file),
        launch_arguments={
            "use_sim_time": "false",
            "params_file": os.path.join(
                get_package_share_directory("turtlebot4_navigation"),
                "config",
                "nav2.yaml"
            ),
            "namespace": "",
        }.items(),
    )

    # RViz2
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", os.path.join(
            os.path.expanduser("~"),
            "src",
            "sllidar_ros2",
            "rviz",
            "sllidar_ros2.rviz"
        )]
    )

    return LaunchDescription([
        # Log messages for successful launch
        LogInfo(msg="Launching TurtleBot4 Robot Description..."),
        robot_description,

        LogInfo(msg="Launching LIDAR Sensor..."),
        lidar,

        LogInfo(msg="Launching SLAM Toolbox..."),
        slam,

        LogInfo(msg="Launching Navigation 2 (Nav2)..."),
        nav2,

        LogInfo(msg="Launching RViz2 for visualization..."),
        rviz,

    ])
