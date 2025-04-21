#!/usr/bin/env python3
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Quaternion
import tf_transformations

class State:
    TO_FORWARD = 1
    ROTATE = 2
    BACK_UP = 3
    TO_HOME = 4
    DONE = 5

class WaypointNavNode(Node):
    def __init__(self):
        super().__init__('waypoint_nav_node')
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.state = State.TO_FORWARD
        self.goal_active = False

        # Publisher for cmd_vel (used during backup)
        self.cmd_vel_pub = self.create_publisher(TwistStamped, 'cmd_vel', 10)

        # Initialize poses for each phase:
        self.forward_pose = PoseStamped()
        self.rotate_pose = PoseStamped()
        self.home_pose = PoseStamped()

        self.set_forward_position()
        self.set_rotate_position()
        self.set_home_position()

        # Timer for state machine
        self.timer = self.create_timer(0.1, self.execute_state_machine)

    def set_forward_position(self):
        # Forward goal: drive straight forward 1.0 meter
        self.forward_pose.header.frame_id = 'map'
        self.forward_pose.pose.position.x = 1.0541
        self.forward_pose.pose.position.y = -0.254
        self.forward_pose.pose.position.z = 0.0
        self.forward_pose.pose.orientation = self.create_quaternion(0.0)

    def set_rotate_position(self):
        # Rotation goal: stay at same position but rotate 100 degrees (converted to radians)
        self.rotate_pose.header.frame_id = 'map'
        self.rotate_pose.pose.position.x = 0.0
        self.rotate_pose.pose.position.y = 0.0
        self.rotate_pose.pose.position.z = 0.0
        self.rotate_pose.pose.orientation = self.create_quaternion(math.radians(100))

    def set_home_position(self):
        # Home goal: return to origin with orientation 0
        self.home_pose.header.frame_id = 'map'
        self.home_pose.pose.position.x = 0.0
        self.home_pose.pose.position.y = 0.0
        self.home_pose.pose.position.z = 0.0
        self.home_pose.pose.orientation = self.create_quaternion(0.0)

    def create_quaternion(self, yaw):
        # Convert roll=0, pitch=0, yaw into a quaternion using tf_transformations
        q = tf_transformations.quaternion_from_euler(0, 0, yaw)
        quat = Quaternion()
        quat.x = q[0]
        quat.y = q[1]
        quat.z = q[2]
        quat.w = q[3]
        return quat

    def execute_state_machine(self):
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("Nav2 action server not available")
            return

        if not self.goal_active:
            if self.state == State.TO_FORWARD:
                self.get_logger().info("Navigating straight forward...")
                self.send_goal(self.forward_pose, self.forward_callback)
                self.goal_active = True

            elif self.state == State.ROTATE:
                self.get_logger().info("Rotating 100 degrees...")
                self.send_goal(self.rotate_pose, self.rotate_callback)
                self.goal_active = True

            elif self.state == State.BACK_UP:
                self.get_logger().info("Backing up...")
                self.backup_robot()
                self.state = State.TO_HOME

            elif self.state == State.TO_HOME:
                self.get_logger().info("Navigating back to home...")
                self.send_goal(self.home_pose, self.home_callback)
                self.goal_active = True

            elif self.state == State.DONE:
                self.get_logger().info("Task complete.")
                self.timer.cancel()

    def send_goal(self, pose, result_callback):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose
        goal_handle_future = self.nav_to_pose_client.send_goal_async(
            goal_msg,
            feedback_callback=None
        )
        goal_handle_future.add_done_callback(lambda future: result_callback(future.result()))

    def forward_callback(self, goal_handle):
        if not goal_handle.accepted:
            self.get_logger().error("Forward goal rejected")
            self.goal_active = False
            return
        self.get_logger().info("Forward goal accepted, waiting for result...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.forward_result_callback)

    def forward_result_callback(self, future):
        result = future.result().result  # This is a NavigateToPose_Result object
        if result.error_code == 0:
            self.get_logger().info("Forward goal reached.")
            self.state = State.ROTATE
        else:
            self.get_logger().warn(f"Forward goal failed with error_code: {result.error_code}")
        self.goal_active = False

    def rotate_callback(self, goal_handle):
        if not goal_handle.accepted:
            self.get_logger().error("Rotate goal rejected")
            self.goal_active = False
            return
        self.get_logger().info("Rotate goal accepted, waiting for result...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.rotate_result_callback)

    def rotate_result_callback(self, future):
        result = future.result().result
        if result.error_code == 0:
            self.get_logger().info("Rotate goal reached.")
            self.state = State.BACK_UP
        else:
            self.get_logger().warn(f"Rotate goal failed with error_code: {result.error_code}")
        self.goal_active = False

    def home_callback(self, goal_handle):
        if not goal_handle.accepted:
            self.get_logger().error("Home goal rejected")
            self.goal_active = False
            return
        self.get_logger().info("Home goal accepted, waiting for result...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.home_result_callback)

    def home_result_callback(self, future):
        result = future.result().result
        if result.error_code == 0:
            self.get_logger().info("Home goal reached.")
            self.state = State.DONE
        else:
            self.get_logger().warn(f"Home goal failed with error_code: {result.error_code}")
        self.goal_active = False

    def backup_robot(self):
        twist_stamped_msg = TwistStamped()
        twist_stamped_msg.header.frame_id = 'base_link'
        twist_stamped_msg.twist.linear.x = -0.2
        twist_stamped_msg.twist.angular.z = 0.0

        rate = self.create_rate(10)
        start_time = time.time()
        while time.time() - start_time < 8.0:
            twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()
            self.cmd_vel_pub.publish(twist_stamped_msg)
            rate.sleep()

        twist_stamped_msg.twist.linear.x = 0.0
        twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()
        self.cmd_vel_pub.publish(twist_stamped_msg)
        self.get_logger().info("Backup complete")

def main(args=None):
    rclpy.init(args=args)
    node = WaypointNavNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()

