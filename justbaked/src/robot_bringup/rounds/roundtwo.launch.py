import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Declare launch arguments for each component
    launch_robot_description = LaunchConfiguration('launch_robot_description')
    launch_lidar = LaunchConfiguration('launch_lidar')
    launch_mov = LaunchConfiguration('launch_mov')
    launch_temp_sens = LaunchConfiguration('launch_temp_sens')
    launch_localization = LaunchConfiguration('launch_localization')
    launch_nav2 = LaunchConfiguration('launch_nav2')
    launch_rviz = LaunchConfiguration('launch_rviz')

    # Get paths to required launch files
    startup_launch_file = os.path.join(
        get_package_share_directory("robot_bringup"),
        "launch",
        "startup.launch.py",
    )

    # Include the startup.launch.py file
    startup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(startup_launch_file),
        launch_arguments={
            'launch_robot_description': launch_robot_description,
            'launch_lidar': launch_lidar,
            'launch_mov': launch_mov,
            'launch_temp_sens': launch_temp_sens,
            'launch_localization': launch_localization,
            'launch_nav2': launch_nav2,
            'launch_rviz': launch_rviz,
        }.items()
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
            default_value='true',
            description='Whether to launch the Localization Toolbox',
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

        # Include the startup.launch.py file
        startup_launch,
    ])


