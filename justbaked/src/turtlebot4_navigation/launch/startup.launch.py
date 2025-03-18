import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, LogInfo, LogError, RegisterEventHandler
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

    # Error Handling: Print error if any process fails
    error_handler = [
        RegisterEventHandler(
            OnProcessExit(
                target_action=robot_description,
                on_exit=[LogError(msg="Error: Robot Description failed to launch!")]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=lidar,
                on_exit=[LogError(msg="Error: LIDAR Sensor failed to launch!")]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=tank_mov,
                on_exit=[LogError(msg="Error: Tank Movement failed to launch!")]
            )
        ),        
        RegisterEventHandler(
            OnProcessExit(
                target_action=slam,
                on_exit=[LogError(msg="Error: SLAM Toolbox failed to launch!")]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=nav2,
                on_exit=[LogError(msg="Error: Navigation 2 (Nav2) failed to launch!")]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=rviz,
                on_exit=[LogError(msg="Error: RViz2 failed to launch!")]
            )
        ),
    ]

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

        # Attach error handlers
        *error_handler,
    ])
