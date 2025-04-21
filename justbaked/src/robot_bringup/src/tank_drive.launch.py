#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TwistStamped
from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import Quaternion
import time
import math


class State:
    TO_START = 1
    TO_WAYPOINT = 2
    BACK_UP = 3
    TO_HOME = 4
    DONE = 5


class WaypointNavNode(Node):
    def __init__(self):
        super().__init__('waypoint_nav_node')
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.state = State.TO_START
        self.goal_active = False  # Track if a goal is currently being processed

        # Publishers
        self.cmd_vel_pub = self.create_publisher(TwistStamped, 'cmd_vel', 10)

        # Initialize poses
        self.start_pose = PoseStamped()
        self.waypoint_pose = PoseStamped()
        self.home_pose = PoseStamped()
        self.set_start_position()
        self.set_waypoint_position()
        self.set_home_position()

        # Timer for state machine
        self.timer = self.create_timer(0.1, self.execute_state_machine)

    def set_start_position(self):
        self.start_pose.header.frame_id = 'map'
        self.start_pose.pose.position.x = 0.0
        self.start_pose.pose.position.y = 0.0
        self.start_pose.pose.position.z = 0.0
        self.start_pose.pose.orientation = self.create_quaternion(0.0)

    def set_waypoint_position(self):
        self.waypoint_pose.header.frame_id = 'map'
        self.waypoint_pose.pose.position.x = 1.054
        self.waypoint_pose.pose.position.y = -0.254
        self.waypoint_pose.pose.position.z = 0.0
        self.waypoint_pose.pose.orientation = self.create_quaternion(math.pi)

    def set_home_position(self):
        self.home_pose.header.frame_id = 'map'
        self.home_pose.pose.position.x = 0.0
        self.home_pose.pose.position.y = 0.0
        self.home_pose.pose.position.z = 0.0
        self.home_pose.pose.orientation = self.create_quaternion(math.pi)

    def create_quaternion(self, yaw):
        q = Quaternion()
        q.w = math.cos(yaw / 2.0)
        q.x = 0.0
        q.y = 0.0
        q.z = math.sin(yaw / 2.0)
        return q

    def execute_state_machine(self):
        if not self.nav_to_pose_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("Nav2 action server not available")
            return

        # Only send new goals if no goal is currently active
        if not self.goal_active:
            if self.state == State.TO_START:
                self.get_logger().info("Navigating to start position...")
                self.send_goal(self.start_pose, self.to_start_callback)
                self.goal_active = True

            elif self.state == State.TO_WAYPOINT:
                self.get_logger().info("Navigating to waypoint...")
                self.send_goal(self.waypoint_pose, self.to_waypoint_callback)
                self.goal_active = True

            elif self.state == State.BACK_UP:
                self.get_logger().info("Backing up...")
                self.backup_robot()
                self.state = State.TO_HOME

            elif self.state == State.TO_HOME:
                self.get_logger().info("Navigating back to home...")
                self.send_goal(self.home_pose, self.to_home_callback)
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
        goal_handle_future.add_done_callback(
            lambda future: self.goal_response_callback(future, result_callback)
        )

    def goal_response_callback(self, future, result_callback):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            self.goal_active = False
            return
        self.get_logger().info("Goal accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(result_callback)

    def to_start_callback(self, future):
        self.get_logger().info(f"Future done: {future.done()}")
        try:
            result = future.result()
            self.get_logger().info(f"Navigation result: {result.navigation_result}")
            if result.navigation_result == 0:
                self.get_logger().info("Reached start position")
                self.state = State.TO_WAYPOINT
            else:
                self.get_logger().warn(f"Navigation failed with result: {result.navigation_result}")
        except Exception as e:
            self.get_logger().error(f"Error in to_start_callback: {e}")
        finally:
            self.goal_active = False

    def to_waypoint_callback(self, future):
        self.get_logger().info(f"Future done: {future.done()}")
        try:
            result = future.result()
            self.get_logger().info(f"Navigation result: {result.navigation_result}")
            if result.navigation_result == 0:
                self.get_logger().info("Reached waypoint position")
                self.state = State.BACK_UP
            else:
                self.get_logger().warn(f"Navigation failed with result: {result.navigation_result}")
        except Exception as e:
            self.get_logger().error(f"Error in to_waypoint_callback: {e}")
        finally:
            self.goal_active = False

    def to_home_callback(self, future):
        self.get_logger().info(f"Future done: {future.done()}")
        try:
            result = future.result()
            self.get_logger().info(f"Navigation result: {result.navigation_result}")
            if result.navigation_result == 0:
                self.get_logger().info("Reached home position")
                self.state = State.DONE
            else:
                self.get_logger().warn(f"Navigation failed with result: {result.navigation_result}")
        except Exception as e:
            self.get_logger().error(f"Error in to_home_callback: {e}")
        finally:
            self.goal_active = False

    def backup_robot(self):
        twist_stamped_msg = TwistStamped()
        twist_stamped_msg.header.frame_id = 'base_link'
        twist_stamped_msg.twist.linear.x = -0.2
        twist_stamped_msg.twist.linear.y = 0.0
        twist_stamped_msg.twist.linear.z = 0.0
        twist_stamped_msg.twist.angular.x = 0.0
        twist_stamped_msg.twist.angular.y = 0.0
        twist_stamped_msg.twist.angular.z = 0.0

        rate = self.create_rate(10)
        start_time = time.time()
        while time.time() - start_time < 5.0:  # Back up for 5 seconds
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

