#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from gpiozero import Servo
import time

class ServoControlNode(Node):
    def __init__(self):
        super().__init__('cat_servo_gpiozero')

        # Set up the servo (GPIO 5 aka Pin 29)
        self.servo = Servo(5)

        # Create a subscription to listen to angle values
        self.subscription = self.create_subscription(
                Int32,
                'servo_angle', # Topic name
                self.listener_callback,
                10
        )
        self.subscription # prevent unused variable warning

    def listener_callback(self, msg):
        angle = msg.data # Get angle from the message
        self.get_logger().info(f"Moving servo to: {angle} degrees")

        # Map the angle to the servo's range of motion (-1 to 1) (Can be adjusted based on servo)
        mapped_value = (angle - 90) / 90 # Map angle (90 degrees as neutral)

        # Move the servo to the mapped position
        self.servo.value = mapped_value
        time.sleep(1)

def main(args=None):
    rclpy.init(args=args)

    node = ServoControlNode()

    try:
        rclpy.spin(node) # Keep the node running and processing messages
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

