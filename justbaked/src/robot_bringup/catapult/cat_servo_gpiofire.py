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

        # Initialize the servo to a neutral position (usually 0 for neutral or 0.5 for centered position)
        self.servo.value = None  # This ensures the servo is neutralized initially (stop twitching)

        # Create a subscription to listen to the /servo_pub topic
        self.subscription = self.create_subscription(
                Int32,
                '/servo_pub',  # Topic name
                self.listener_callback,
                10
        )
        self.subscription  # Prevent unused variable warning

    def listener_callback(self, msg):
        angle = msg.data  # Get angle value from the message
        if angle == 360:
            self.get_logger().info(f"Received angle: {angle} degrees. Moving servo.")

            # Map the angle to the servo's range of motion (-1 to 1)
            # Assuming 36 degrees as the maximum limit for this example
            mapped_value = (angle - 90) / 90  # Map angle (90 degrees as neutral)

            # Move the servo to the mapped position
            self.servo.value = mapped_value
            time.sleep(1)
        else:
            self.get_logger().info(f"Received angle: {angle} degrees. Ignoring, as only 36 degrees triggers movement.")

def main(args=None):
    rclpy.init(args=args)

    node = ServoControlNode()

    try:
        rclpy.spin(node)  # Keep the node running and processing messages
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

