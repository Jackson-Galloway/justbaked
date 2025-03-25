#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import RPi.GPIO as GPIO

class ButtonPublisher(Node):
    def __init__(self):
        super().__init__('button_publisher')
        self.publisher = self.create_publisher(Int32, '/round', 10)

        # GPIO pins for buttons (adjust as needed)
        self.button_pins = {
            17: 1,  # Button for Round 1 (GPIO 17)
            27: 2,  # Button for Round 2 (GPIO 27)
            22: 3   # Button for Round 3 (GPIO 22)
        }

        GPIO.setmode(GPIO.BCM)
        for pin in self.button_pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.button_callback, bouncetime=300)

        self.get_logger().info("Button publisher started, waiting for button presses")

    def button_callback(self, channel):
        round_num = self.button_pins[channel]
        self.get_logger().info(f"Button for Round {round_num} pressed")
        msg = Int32()
        msg.data = round_num
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ButtonPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down button publisher")
    finally:
        GPIO.cleanup()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
