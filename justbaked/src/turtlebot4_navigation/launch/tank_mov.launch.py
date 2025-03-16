from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlebot4_navigation',
            executable='TankDemo.py',
            name='motor_controller',
            output='screen'
        )
    ])




