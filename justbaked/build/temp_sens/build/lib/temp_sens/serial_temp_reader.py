#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import serial

class SerialTempReader(Node):
    def __init__(self):
        super().__init__('serial_temp_reader')
        self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)  # Force debug logging
        self.get_logger().info("Starting serial temp reader")
        self.publisher = self.create_publisher(Float32, 'temperature', 10)
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
            self.get_logger().info(f"Opened serial port: /dev/ttyACM0 at 9600 baud")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to open serial port: {e}")
            raise e
        self.timer = self.create_timer(1.0, self.read_serial)
        self.buffer = ""

    def read_serial(self):
        try:
            if self.serial_port.in_waiting > 0:
                # Read all available data
                data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                #self.get_logger().debug(f"Data available: {len(data)} bytes")
                self.buffer += data
                #self.get_logger().debug(f"Buffer after read: {self.buffer}")
            else:
                self.get_logger().debug("No data available on serial port")

            # Split the buffer into lines, handling both \n and \r\n
            lines = self.buffer.splitlines()
            # Keep the last line in the buffer if it's incomplete
            if not self.buffer.endswith(('\n', '\r')):
                self.buffer = lines[-1]
                lines = lines[:-1]
            else:
                self.buffer = ""
                lines = lines

            #self.get_logger().debug(f"Processing lines: {lines}")

            for line in lines:
                line = line.strip()  # Remove \r or \n from the line itself
                if not line:  # Skip empty lines
                    continue
               #self.get_logger().info(f"Received line: {line}")

                temp_f = float(line)  # Convert the line to a float (Fahrenheit)
                msg = Float32()
                msg.data = temp_f
                self.publisher.publish(msg)
                #self.get_logger().info(f"Published temperature: {temp_f:.2f} F")

        except serial.SerialException as e:
            self.get_logger().error(f"Error reading serial: {e}")

    def destroy_node(self):
        self.serial_port.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SerialTempReader()
    try:
        rclpy.spin(node)
    except Exception as e:
        node.get_logger().error(f"Unexpected error: {e}")
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except rclpy._rclpy_pybind11.RCLError as e:
            print(f"Warning: Ignoring shutdown error: {e}")

if __name__ == '__main__':
    main()
