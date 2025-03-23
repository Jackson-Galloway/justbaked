#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature
import smbus
import time

class MLX90614Node(Node):
    def __init__(self):
        super().__init__('mlx90614_node')
        self.publisher = self.create_publisher(Temperature, 'temperature', 10)
        self.bus = smbus.SMBus(1)  # I2C bus 1 on Raspberry Pi
        self.address = 0x5A  # MLX90614 default I2C address
        self.timer = self.create_timer(1.0, self.read_temperature)  # Read every second

    def read_temperature(self):
        try:
            # Read ambient and object temperatures (registers 0x06 and 0x07)
            raw_ambient = self.bus.read_word_data(self.address, 0x06)
            raw_object = self.bus.read_word_data(self.address, 0x07)

            # Convert raw data to temperature in Celsius
            ambient_temp = (raw_ambient * 0.02) - 273.15
            object_temp = (raw_object * 0.02) - 273.15

            # Publish object temperature
            msg = Temperature()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "base_link"
            msg.temperature = object_temp
            msg.variance = 0.0  # Assuming no variance data
            self.publisher.publish(msg)
            self.get_logger().info(f'Object Temperature: {object_temp:.2f} °C')

        except Exception as e:
            self.get_logger().error(f'Failed to read temperature: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    node = MLX90614Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
