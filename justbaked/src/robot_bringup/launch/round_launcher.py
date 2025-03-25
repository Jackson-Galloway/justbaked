#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import subprocess

class RoundLauncher(Node):
    def __init__(self):
        super().__init__('round_launcher')
        self.subscription = self.create_subscription(
            Int32,
            '/round',
            self.round_callback,
            10
        )
        self.process = None
        self.get_logger().info("Round launcher started, waiting for round selection")

    def round_callback(self, msg):
        round_num = msg.data
        if self.process is not None and self.process.poll() is None:
            self.get_logger().warning("A round is already running, terminating it")
            self.process.terminate()
            self.process.wait()

        launch_file = f"round{round_num}.launch.py"
        self.get_logger().info(f"Launching {launch_file} for Round {round_num}")
        try:
            self.process = subprocess.Popen(['ros2', 'launch', 'robot_bringup', launch_file])
        except Exception as e:
            self.get_logger().error(f"Failed to launch {launch_file}: {e}")

    def destroy_node(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = RoundLauncher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down round launcher")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
