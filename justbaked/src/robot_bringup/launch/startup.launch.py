import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, TimerAction
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Declare launch arguments for each component
    launch_robot_description = LaunchConfiguration('launch_robot_description')
    launch_lidar = LaunchConfiguration('launch_lidar')
    launch_mov = LaunchConfiguration('launch_mov')
    launch_temp_sens = LaunchConfiguration('launch_temp_sens')
    launch_localization = LaunchConfiguration('launch_localization')
    launch_slam = LaunchConfiguration('launch_slam')
    launch_nav2 = LaunchConfiguration('launch_nav2')
    launch_rviz = LaunchConfiguration('launch_rviz')

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
    localization_launch_file = os.path.join(
        get_package_share_directory("turtlebot4_navigation"),
        "launch",
        "localization.launch.py",
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
        condition=IfCondition(launch_robot_description)
    )

    # LIDAR Sensor
    lidar = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch_file),
        condition=IfCondition(launch_lidar)
    )

    # Tank Movement
    mov = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(mov_launch_file),
        condition=IfCondition(launch_mov)
    )

    # Temperature Sensor
    temp_sens = Node(
        package='temp_sens',
        executable='serial_temp_reader',
        name='serial_temp_reader',
        output='screen',
        condition=IfCondition(launch_temp_sens)
    )

    # Localization
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(localization_launch_file),
        condition=IfCondition(launch_localization),
        launch_arguments={
            "use_sim_time": "false",
            "params_file": os.path.join(
                get_package_share_directory("turtlebot4_navigation"),
                "config",
                "localization.yaml"
            ),
        }.items(),
        condition=IfCondition(launch_localization)
    )

    # SLAM Toolbox
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch_file),
        condition=IfCondition(launch_slam)
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
        condition=IfCondition(launch_nav2)
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
        )],
        condition=IfCondition(launch_rviz)
    )

    return LaunchDescription([
        # Declare launch arguments
        DeclareLaunchArgument(
            'launch_robot_description',
            default_value='true',
            description='Whether to launch the robot description',
            choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'launch_lidar',
            default_value='true',
            description='Whether to launch the LIDAR sensor',
            choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'launch_mov',
            default_value='true',
            description='Whether to launch the tank movement',
            choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'launch_temp_sens',
            default_value='true',
            description='Whether to launch the temperature sensor',
            choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'launch_localization',
            default_value='false', # Set to false to avoid conflicts with SLAM Toolbox
            description='Whether to launch localization',
            choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'launch_slam',
            default_value='true',
            description='Whether to launch the SLAM Toolbox',
            choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'launch_nav2',
            default_value='true',
            description='Whether to launch Navigation 2 (Nav2)',
            choices=['true', 'false']
        ),
        DeclareLaunchArgument(
            'launch_rviz',
            default_value='true',
            description='Whether to launch RViz2 for visualization',
            choices=['true', 'false']
        ),

        # Robot description
        LogInfo(msg="Launching TurtleBot4 Robot Description...", condition=IfCondition(launch_robot_description)),
        robot_description,

        # LIDAR (delayed by 2 seconds)
        TimerAction(
            period=2.0,
            actions=[
                LogInfo(msg="Launching LIDAR Sensor...", condition=IfCondition(launch_lidar)),
                lidar,
            ],
            condition=IfCondition(launch_lidar)
        ),

        # Tank Movement (delayed by 4 seconds)
        TimerAction(
            period=4.0,
            actions=[
                LogInfo(msg="Launching Tank Mov...", condition=IfCondition(launch_mov)),
                mov,
            ],
            condition=IfCondition(launch_mov)
        ),

        # Temperature Sensor (delayed by 6 seconds)
        TimerAction(
            period=6.0,
            actions=[
                LogInfo(msg="Launching Temperature Sensor...", condition=IfCondition(launch_temp_sens)),
                temp_sens,
            ],
            condition=IfCondition(launch_temp_sens)
        ),

        # Localization (delayed by 8 seconds)
        TimerAction(
            period=8.0,
            actions=[
                LogInfo(msg="Launching Localization...", condition=IfCondition(launch_localization)),
                localization,
            ],
            condition=IfCondition(launch_localization)
        ),

        # SLAM Toolbox (delayed by 8 seconds)
        TimerAction(
            period=8.0,
            actions=[
                LogInfo(msg="Launching SLAM Toolbox...", condition=IfCondition(launch_slam)),
                slam,
            ],
            condition=IfCondition(launch_slam)
        ),

        # Nav2 (delayed by 12 seconds)
        TimerAction(
            period=12.0,
            actions=[
                LogInfo(msg="Launching Navigation 2 (Nav2)...", condition=IfCondition(launch_nav2)),
                nav2,
            ],
            condition=IfCondition(launch_nav2)
        ),

        # RViz (delayed by 20 seconds)
        TimerAction(
            period=20.0,
            actions=[
                LogInfo(msg="Launching RViz2 for visualization...", condition=IfCondition(launch_rviz)),
                rviz,
            ],
            condition=IfCondition(launch_rviz)
        ),
    ])
