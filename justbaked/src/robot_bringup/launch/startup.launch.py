import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, LogInfo, RegisterEventHandler, TimerAction, EmitEvent
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.event_handlers import OnShutdown
from launch.events import Shutdown
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get paths to required launch files
    turtlebot4_description_launch = os.path.join(
        get_package_share_directory("turtlebot4_description"),
        "launch",
        "robot_description.launch.py",
    )

    lidar_launch_file = os.path.join(
        get_package_share_directory("sllidar_ros2"),
        "launch",
        "sllidar_a1_launch.py",
    )

    mov_launch_file = os.path.join(
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

    # Robot_Mov
    mov = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(mov_launch_file)
    )

    # SLAM Toolbox
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_file),
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
            "justbaked",
            "justbaked",
            "src",
            "turtlebot4_description",
            "robdesc.rviz",
        )]
    )

    # Shutdown handler with delays
    shutdown_handler = RegisterEventHandler(
        OnShutdown(
            on_shutdown=[
                LogInfo(msg="RViz2 has exited, starting shutdown sequence..."),
                TimerAction(
                    period=5.0,
                    actions=[
                        LogInfo(msg="Shutting down Nav2..."),
                    ]
                ),
                TimerAction(
                    period=10.0,
                    actions=[
                        LogInfo(msg="Shutting down SLAM Toolbox..."),
                    ]
                ),
                TimerAction(
                    period=15.0,
                    actions=[
                        LogInfo(msg="Shutting down Tank Mov..."),
                    ]
                ),
                TimerAction(
                    period=20.0,
                    actions=[
                        LogInfo(msg="Shutting down LIDAR Sensor..."),
                    ]
                ),
                TimerAction(
                    period=25.0,
                    actions=[
                        LogInfo(msg="Shutting down Robot Description..."),
                        EmitEvent(event=Shutdown(reason="Launch completed")),
                    ]
                ),
            ]
        )
    )

    return LaunchDescription([
        # Log and launch robot description immediately
        LogInfo(msg="Launching TurtleBot4 Robot Description..."),
        robot_description,

        # Delay LIDAR launch by 5 seconds
        TimerAction(
            period=5.0,
            actions=[
                LogInfo(msg="Launching LIDAR Sensor..."),
                lidar,
            ]
        ),

        # Delay Mov launch by 10 second
        TimerAction(
            period=10.0,
            actions=[
                LogInfo(msg="Launching Tank Mov..."),
                mov,
            ]
        ),

        # Delay SLAM launch by 15 seconds
        TimerAction(
            period=15.0,
            actions=[
                LogInfo(msg="Launching SLAM Toolbox..."),
                slam,
            ]
        ),

        # Delay Nav2 launch by 20 seconds
        TimerAction(
            period=20.0,
            actions=[
                LogInfo(msg="Launching Navigation 2 (Nav2)..."),
                nav2,
            ]
        ),

        # Delay RViz launch by 25 seconds
        TimerAction(
            period=25.0,
            actions=[
                LogInfo(msg="Launching RViz2 for visualization..."),
                rviz,
            ]
        ),

        # Attach shutdown handler
        shutdown_handler,
    ])
