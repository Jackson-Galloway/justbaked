from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import PathJoinSubstitution

def generate_launch_description():
    pkg_turtlebot4_description = get_package_share_directory('turtlebot4_description')
    pkg_sllidar_ros2 = get_package_share_directory('sllidar_ros2')
    pkg_turtlebot4_navigation = get_package_share_directory('turtlebot4_navigation')
    pkg_rviz2 = get_package_share_directory('rviz2')

    robot_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_turtlebot4_description, 'launch', 'robot_description.launch.py']))
    )

    sllidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_sllidar_ros2, 'launch', 'sllidar_a1_launch.py']))
    )

    tank_mov_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_turtlebot4_navigation, 'launch', 'tank_mov.launch.py']))
    )

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_turtlebot4_navigation, 'launch', 'slam.launch.py']))
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_turtlebot4_navigation, 'launch', 'nav2.launch.py']))
    )

    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', PathJoinSubstitution([pkg_turtlebot4_description, 'launch', 'robdesc.rviz'])]
    )

    return LaunchDescription([
        robot_description_launch,
        RegisterEventHandler(
            OnProcessExit(
                target_action=robot_description_launch,
                on_exit=[LogInfo(msg="Robot description launched"), sllidar_launch]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=sllidar_launch,
                on_exit=[LogInfo(msg="SLLIDAR launched"), tank_mov_launch]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=tank_mov_launch,
                on_exit=[LogInfo(msg="Tank movement launched"), slam_launch]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=slam_launch,
                on_exit=[LogInfo(msg="SLAM launched"), nav2_launch]
            )
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=nav2_launch,
                on_exit=[LogInfo(msg="Navigation launched"), rviz2_node]
            )
        )
    ])
