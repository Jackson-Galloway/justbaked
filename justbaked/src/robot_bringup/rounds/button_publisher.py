#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from gpiozero import Button
import subprocess


class ButtonPublisher(Node):
    def __init__(self):
        super().__init__('button_publisher')
        self.publisher = self.create_publisher(Int32, '/round', 10)
        self.round_selected = False

        # Map GPIO pin to round number
        self.pin_to_round = {
            17: 1,  # GPIO17 = Round 1
            27: 2,  # GPIO27 = Round 2
            22: 3   # GPIO22 = Round 3
        }

        # Initialize buttons with pull-up resistors
        self.buttons = {
            pin: Button(pin, pull_up=True)
            for pin in self.pin_to_round
        }

        # Set up callbacks for each button
        for pin, button in self.buttons.items():
            button.when_pressed = lambda pin=pin: self.handle_press(pin)

        self.get_logger().info("ButtonPublisher started. Waiting for button press...")

    def handle_press(self, pin):
        if self.round_selected:
            return

        round_num = self.pin_to_round[pin]
        self.round_selected = True
        self.get_logger().info(f"GPIO {pin} pressed — launching Round {round_num}")

        # Publish round selection
        msg = Int32()
        msg.data = round_num
        self.publisher.publish(msg)

        # Launch corresponding round launch file
        self.launch_round_file(round_num)

    def launch_round_file(self, round_num):
        try:
            package_name = 'robot_bringup'
            round_to_filename = {
                1: 'roundone.launch.py',
                2: 'roundtwo.launch.py',
                3: 'roundthree.launch.py'
            }

            launch_file = round_to_filename.get(round_num)
            if not launch_file:
                self.get_logger().error(f"No launch file found for round {round_num}")
                return

            self.get_logger().info(f"Launching: ros2 launch {package_name} {launch_file}")
            subprocess.Popen(
                f"ros2 launch {package_name} {launch_file}",
                shell=True,
                executable="/bin/bash"
            )

        except Exception as e:
            self.get_logger().error(f"Failed to launch round {round_num}: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ButtonPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down ButtonPublisher")
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()

