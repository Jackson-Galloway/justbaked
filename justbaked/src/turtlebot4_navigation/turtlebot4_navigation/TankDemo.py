#!/usr/bin/env python3

import smbus
import time
import struct
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped, Quaternion, TransformStamped
from nav_msgs.msg import Odometry
import tf_transformations
from math import sin, cos
import tf2_ros

# (Set the I2C bus number, usually 1)
I2C_BUS = 1

# (Set the I2C address of the 4-ch encoder motor driver)
MOTOR_ADDR = 0x34 

# (Register address)
ADC_BAT_ADDR = 0x00
MOTOR_TYPE_ADDR = 0x14 # Set the encoder motor type
MOTOR_ENCODER_POLARITY_ADDR = 0x15 # Set the polarity of the encoder
MOTOR_FIXED_PWM_ADDR = 0x1F # Fixed PWM control, open-loop control, range: (-100~100)
MOTOR_FIXED_SPEED_ADDR = 0x33 # Fixed speed control, closed-loop control
MOTOR_ENCODER_TOTAL_ADDR = 0x3C # Total pulse value of each of the four encoder motors

# (Motor type values)
MOTOR_TYPE_JGB37_520_12V_110RPM = 3 # Magnetic ring rotates 44 pulses per revolution, reduction ratio: 90, default

# (Motor type and encoder direction polarity)
MotorType = MOTOR_TYPE_JGB37_520_12V_110RPM
MotorEncoderPolarity = 0

bus = smbus.SMBus(I2C_BUS)

class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')
        self.subscription = self.create_subscription(
            TwistStamped,
            '/cmd_vel',
            self.cmd_vel_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.motor_init()
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()
        self.last_encoder_left = 0
        self.last_encoder_right = 0

        # Create a timer to call update_odometry regularly
        self.timer = self.create_timer(0.1, self.update_odometry)  # Update odometry at 10 Hz

    def motor_init(self):
        print("Initializing motor...")
        try:
            bus.write_byte_data(MOTOR_ADDR, MOTOR_TYPE_ADDR, MotorType)  # Set the motor type
            time.sleep(0.5)
            bus.write_byte_data(MOTOR_ADDR, MOTOR_ENCODER_POLARITY_ADDR, MotorEncoderPolarity)  # Set the polarity of the encoder
            print("Motor initialized.")
        except OSError as e:
            print(f"Failed to initialize motor: {e}")

    def cmd_vel_callback(self, msg):
        # Extract linear and angular velocities from the Twist message
        linear_x = msg.twist.linear.x
        angular_z = msg.twist.angular.z

        # Translate velocities to motor speeds
        left_speed = int((linear_x - angular_z) * 50)  # Adjust the scaling factor as needed
        right_speed = int((linear_x + angular_z) * 50)  # Adjust the scaling factor as needed

        # Ensure the speeds are within the valid range
        left_speed = max(min(left_speed, 100), -100)
        right_speed = max(min(right_speed, 100), -100)

        # Send motor speed commands via I2C
        speed_command = [left_speed, right_speed]
        print(f"Sending speed command: {speed_command}")
        try:
            bus.write_i2c_block_data(MOTOR_ADDR, MOTOR_FIXED_SPEED_ADDR, speed_command)
        except OSError as e:
            print(f"Failed to send speed command: {e}")

    def update_odometry(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9  # Convert to seconds

        # Read encoder values
        try:
            encoder_data = struct.unpack('iiii', bytes(bus.read_i2c_block_data(MOTOR_ADDR, MOTOR_ENCODER_TOTAL_ADDR, 16)))
            encoder_left = encoder_data[0]
            encoder_right = encoder_data[1]
            print(f"Encoder left: {encoder_left}, Encoder right: {encoder_right}")
        except OSError as e:
            print(f"Failed to read encoder data: {e}")
            return

        # Calculate the change in encoder values
        delta_left = encoder_left - self.last_encoder_left
        delta_right = encoder_right - self.last_encoder_right

        # Update last encoder values
        self.last_encoder_left = encoder_left
        self.last_encoder_right = encoder_right

        # Assuming wheel separation and wheel radius
        wheel_separation = 0.5  # Distance between wheels in meters
        wheel_radius = 0.1  # Radius of the wheels in meters
        encoder_resolution = 44  # Pulses per revolution

        # Calculate distances traveled by each wheel
        distance_left = (delta_left / encoder_resolution) * (2 * 3.14159 * wheel_radius)
        distance_right = (delta_right / encoder_resolution) * (2 * 3.14159 * wheel_radius)

        # Calculate velocities
        v_left = distance_left / dt
        v_right = distance_right / dt
        v = (v_left + v_right) / 2.0
        omega = (v_right - v_left) / wheel_separation

        # Update position
        self.x += v * dt * cos(self.theta)
        self.y += v * dt * sin(self.theta)
        self.theta += omega * dt

        # Create quaternion from yaw
        odom_quat = tf_transformations.quaternion_from_euler(0, 0, self.theta)

        # Create and publish odometry message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'

        # Set the position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = Quaternion(*odom_quat)

        # Set the velocity
        odom.child_frame_id = 'base_link'
        odom.twist.twist.linear.x = v
        odom.twist.twist.linear.y = 0.0
        odom.twist.twist.angular.z = omega

        # Publish the message
        self.odom_publisher.publish(odom)

        # Publish the transform
        transform = TransformStamped()
        transform.header.stamp = current_time.to_msg()
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_link'
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0
        transform.transform.rotation = Quaternion(*odom_quat)

        print(f"Publishing transform: {transform}")
        self.tf_broadcaster.sendTransform(transform)

        self.last_time = current_time

def main(args=None):
    rclpy.init(args=args)
    motor_controller = MotorController()
    rclpy.spin(motor_controller)
    motor_controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()