from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    startup_launch_file = os.path.join(
        get_package_share_directory('robot_bringup'),
        'launch',
        'startup.launch.py'
    )

    return LaunchDescription([
        # Declare arguments to override defaults in startup.launch.py
        DeclareLaunchArgument(
            'launch_robot_description',
            default_value='true',
            description='Whether to launch the robot description'
        ),
        DeclareLaunchArgument(
            'launch_lidar',
            default_value='true',
            description='Whether to launch the LIDAR sensor'
        ),
        DeclareLaunchArgument(
            'launch_mov',
            default_value='true',
            description='Whether to launch the tank movement'
        ),
        DeclareLaunchArgument(
            'launch_temp_sens',
            default_value='true',
            description='Whether to launch the temperature sensor'
        ),
        DeclareLaunchArgument(
            'launch_slam',
            default_value='false',  # Disable SLAM, use saved map
            description='Whether to launch the SLAM Toolbox'
        ),
        DeclareLaunchArgument(
            'launch_nav2',
            default_value='true',
            description='Whether to launch Navigation 2 (Nav2)'
        ),
        DeclareLaunchArgument(
            'launch_rviz',
            default_value='true',
            description='Whether to launch RViz2 for visualization'
        ),
        DeclareLaunchArgument(
            'launch_waypoint_nav',
            default_value='true',
            description='Whether to launch the waypoint navigation node'
        ),

        # Include startup.launch.py with the specified arguments
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(startup_launch_file),
            launch_arguments={
                'launch_robot_description': 'true',
                'launch_lidar': 'true',
                'launch_mov': 'true',
                'launch_temp_sens': 'true',
                'launch_slam': 'false',
                'launch_nav2': 'true',
                'launch_rviz': 'true',
                'launch_waypoint_nav': 'true'
            }.items()
        )
    ])
