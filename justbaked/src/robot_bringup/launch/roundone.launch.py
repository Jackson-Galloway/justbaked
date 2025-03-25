##!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import PoseStamped, Quaternion
from std_msgs.msg import Float32, Bool
from nav2_msgs.srv import SaveMap
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import tf_transformations
import math
import time
import os
import yaml

def generate_launch_description():
    # Declare launch arguments for each component
    launch_robot_description = LaunchConfiguration('launch_robot_description')
    launch_lidar = LaunchConfiguration('launch_lidar')
    launch_mov = LaunchConfiguration('launch_mov')
    launch_temp_sens = LaunchConfiguration('launch_temp_sens')
    launch_slam = LaunchConfiguration('launch_slam')
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
            'launch_slam': launch_slam,
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

        # Include the startup.launch.py file
        startup_launch,
    ])

class WaypointNavigationNode(Node):
    def __init__(self):
        super().__init__('waypoint_navigation_node')
        self.get_logger().info("Starting waypoint navigation node")

        # Action client for NavigateToPose
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Service client for saving the map
        self.save_map_client = self.create_client(SaveMap, 'map_server/save_map')

        # Subscriber for temperature readings
        self.temperature = None
        self.temperature_sub = self.create_subscription(
            Float32,
            '/temperature',
            self.temperature_callback,
            10
        )

        # Subscriber for start button
        self.start_sub = self.create_subscription(
            Bool,
            '/start',
            self.start_callback,
            10
        )

        # Define waypoints with offsets (1.75 feet = 0.5334 meters)
        self.waypoints = [
            (1.9066, 0.0, 0.0),           # Offset from Corner 2
            (2.44, 1.9066, math.pi / 2), # Offset from Corner 3
            (0.5334, 2.44, math.pi),      # Offset from Corner 4
        ]
        self.starting_position = (0.0, 0.0, 0.0)  # Starting position (Corner 1)
        self.current_waypoint_index = 0
        self.received_initial_pose = False
        self.navigating = False
        self.started = False

        # Track temperatures and waypoints
        self.temperature_readings = []
        self.fire_waypoint = None

        # Paths for saving map and fire waypoint
        self.map_dir = os.path.expanduser("~/justbaked/justbaked/src/robot_bringup/maps")
        self.map_path = os.path.join(self.map_dir, "arena_map")
        self.fire_waypoint_path = os.path.join(self.map_dir, "fire_waypoint.yaml")

        # Check if a saved map and fire waypoint exist (future rounds)
        self.is_first_round = not (os.path.exists(self.map_path + ".pgm") and os.path.exists(self.fire_waypoint_path))
        if not self.is_first_round:
            self.get_logger().info("Detected saved map and fire waypoint, running future round mode")
            self.load_fire_waypoint()
        else:
            self.get_logger().info("No saved map or fire waypoint found, running first round mode")

        # Timer to check initial pose (for first round)
        if self.is_first_round:
            self.timer = self.create_timer(1.0, self.check_initial_pose)

    def temperature_callback(self, msg):
        self.temperature = msg.data
        self.get_logger().info(f"Received temperature: {self.temperature} F")

    def start_callback(self, msg):
        if msg.data and not self.started:
            self.get_logger().info("Start button pressed, beginning navigation")
            self.started = True
            if self.is_first_round:
                self.navigate_to_next_waypoint()
            else:
                self.navigate_to_fire_waypoint()

    def check_initial_pose(self):
        # Wait until AMCL has a good initial pose (for first round)
        if not self.received_initial_pose:
            self.get_logger().info("Waiting for initial pose from AMCL...")
            # Assume initial pose is set manually in RViz
            self.received_initial_pose = True
            self.get_logger().info("Initial pose received, waiting for start button")

    def navigate_to_next_waypoint(self):
        if self.navigating or not self.started:
            return

        if self.current_waypoint_index < len(self.waypoints):
            waypoint = self.waypoints[self.current_waypoint_index]
            self.get_logger().info(f"Navigating to waypoint {self.current_waypoint_index + 1}: {waypoint}")

            # Create the goal pose
            goal_pose = self.create_goal_pose(waypoint[0], waypoint[1], waypoint[2])

            # Send the goal
            self.navigating = True
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = goal_pose
            self.nav_to_pose_client.wait_for_server()
            self._send_goal_future = self.nav_to_pose_client.send_goal_async(
                goal_msg,
                feedback_callback=self.feedback_callback
            )
            self._send_goal_future.add_done_callback(self.goal_response_callback)
        else:
            # All waypoints visited, process temperatures and return to start
            self.process_temperatures()
            self.return_to_start()

    def create_goal_pose(self, x, y, yaw):
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.position.z = 0.0
        quaternion = tf_transformations.quaternion_from_euler(0, 0, yaw)
        goal_pose.pose.orientation = Quaternion(
            x=quaternion[0],
            y=quaternion[1],
            z=quaternion[2],
            w=quaternion[3]
        )
        return goal_pose

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected by server!")
            self.navigating = False
            return

        self.get_logger().info("Goal accepted by server, waiting for result")
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f"Distance to goal: {feedback.distance_to_goal:.2f} meters")

    def get_result_callback(self, future):
        result = future.result()
        if result.status == 4:  # STATUS_SUCCEEDED
            self.get_logger().info("Reached waypoint successfully!")
            # Wait for a temperature reading
            self.wait_for_temperature()
        else:
            self.get_logger().error(f"Failed to reach waypoint, status: {result.status}")
        self.navigating = False
        self.current_waypoint_index += 1
        self.navigate_to_next_waypoint()

    def wait_for_temperature(self):
        self.get_logger().info("Waiting for temperature reading...")
        start_time = time.time()
        timeout = 10.0
        self.temperature = None

        while time.time() - start_time < timeout:
            if self.temperature is not None:
                waypoint = self.waypoints[self.current_waypoint_index]
                self.get_logger().info(
                    f"Temperature at waypoint {self.current_waypoint_index + 1} ({waypoint[0]}, {waypoint[1]}): {self.temperature} F"
                )
                self.temperature_readings.append((self.temperature, waypoint))
                return
            time.sleep(0.1)

        self.get_logger().warning("No temperature reading received within timeout!")

    def process_temperatures(self):
        if not self.temperature_readings:
            self.get_logger().warning("No temperature readings recorded!")
            return

        # Find the waypoint with the highest temperature
        self.fire_waypoint = max(self.temperature_readings, key=lambda x: x[0])[1]
        self.get_logger().info(f"Fire waypoint set to: {self.fire_waypoint}")

    def return_to_start(self):
        self.get_logger().info("Navigating back to starting position: (0, 0, 0)")
        goal_pose = self.create_goal_pose(self.starting_position[0], self.starting_position[1], self.starting_position[2])

        self.navigating = True
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = goal_pose
        self.nav_to_pose_client.wait_for_server()
        self._send_goal_future = self.nav_to_pose_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.return_goal_response_callback)

    def return_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Return goal rejected by server!")
            self.navigating = False
            return

        self.get_logger().info("Return goal accepted by server, waiting for result")
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.return_get_result_callback)

    def return_get_result_callback(self, future):
        result = future.result()
        if result.status == 4:  # STATUS_SUCCEEDED
            self.get_logger().info("Successfully returned to starting position!")
            if self.is_first_round:
                self.save_map_and_fire_waypoint()
        else:
            self.get_logger().error(f"Failed to return to starting position, status: {result.status}")
        self.navigating = False
        self.get_logger().info("Waypoint navigation complete!")

    def save_map_and_fire_waypoint(self):
        # Ensure the maps directory exists
        os.makedirs(self.map_dir, exist_ok=True)

        # Save the map
        self.get_logger().info(f"Saving map to {self.map_path}")
        request = SaveMap.Request()
        request.map_topic = '/map'
        request.map_url = self.map_path
        request.image_format = 'pgm'
        request.map_mode = 'trinary'
        request.free_thresh = 0.25
        request.occupied_thresh = 0.65

        self.save_map_client.wait_for_service()
        future = self.save_map_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None and future.result().success:
            self.get_logger().info("Map saved successfully!")
        else:
            self.get_logger().error("Failed to save map!")

        # Save the fire waypoint
        if self.fire_waypoint:
            fire_waypoint_data = {
                'fire_waypoint': {
                    'x': self.fire_waypoint[0],
                    'y': self.fire_waypoint[1],
                    'yaw': self.fire_waypoint[2]
                }
            }
            with open(self.fire_waypoint_path, 'w') as f:
                yaml.dump(fire_waypoint_data, f)
            self.get_logger().info(f"Fire waypoint saved to {self.fire_waypoint_path}")

    def load_fire_waypoint(self):
        with open(self.fire_waypoint_path, 'r') as f:
            data = yaml.safe_load(f)
            self.fire_waypoint = (
                data['fire_waypoint']['x'],
                data['fire_waypoint']['y'],
                data['fire_waypoint']['yaw']
            )
        self.get_logger().info(f"Loaded fire waypoint: {self.fire_waypoint}")

    def navigate_to_fire_waypoint(self):
        if not self.fire_waypoint:
            self.get_logger().error("No fire waypoint available!")
            return

        self.get_logger().info(f"Navigating to fire waypoint: {self.fire_waypoint}")
        goal_pose = self.create_goal_pose(
            self.fire_waypoint[0],
            self.fire_waypoint[1],
            self.fire_waypoint[2]
        )

        self.navigating = True
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = goal_pose
        self.nav_to_pose_client.wait_for_server()
        self._send_goal_future = self.nav_to_pose_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.fire_goal_response_callback)

    def fire_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Fire waypoint goal rejected by server!")
            self.navigating = False
            return

        self.get_logger().info("Fire waypoint goal accepted by server, waiting for result")
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.fire_get_result_callback)

    def fire_get_result_callback(self, future):
        result = future.result()
        if result.status == 4:  # STATUS_SUCCEEDED
            self.get_logger().info("Reached fire waypoint successfully!")
            # Optionally record temperature again
            self.wait_for_temperature()
        else:
            self.get_logger().error(f"Failed to reach fire waypoint, status: {result.status}")
        self.navigating = False
        self.get_logger().info("Fire waypoint navigation complete!")

def main(args=None):
    rclpy.init(args=args)
    node = WaypointNavigationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down waypoint navigation node")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
