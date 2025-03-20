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
MOTOR_TYPE_ADDR = 0x14  # Set the encoder motor type
MOTOR_ENCODER_POLARITY_ADDR = 0x15  # Set the polarity of the encoder
MOTOR_FIXED_PWM_ADDR = 0x1F         # Fixed PWM control, open-loop control, range: (-100~100)
MOTOR_FIXED_SPEED_ADDR = 0x33       # Fixed speed control, closed-loop control
MOTOR_ENCODER_TOTAL_ADDR = 0x3C     # Total pulse value of each of the four encoder motors

# (Motor type values)
MOTOR_TYPE_JGB37_520_12V_110RPM = 3  # Magnetic ring rotates 44 pulses per revolution, reduction ratio: 90

# (Motor type and encoder direction polarity)
MotorType = MOTOR_TYPE_JGB37_520_12V_110RPM
MotorEncoderPolarity = 0

bus = smbus.SMBus(I2C_BUS)


# -------------------------------------------------------------------------
# 1) Median Filter Class
# -------------------------------------------------------------------------
class MedianFilter:
    """
    A simple Median Filter that stores the last N values
    and returns the median of that window.
    """
    def __init__(self, size=5):
        self.size = size
        self.buffer = []

    def filter(self, new_value):
        self.buffer.append(new_value)
        if len(self.buffer) > self.size:
            self.buffer.pop(0)
        sorted_window = sorted(self.buffer)
        mid_index = len(sorted_window) // 2
        return sorted_window[mid_index]


# -------------------------------------------------------------------------
# 2) Moving Average Filter Class
# -------------------------------------------------------------------------
class MovingAverageFilter:
    """
    A simple Moving Average Filter that stores the last N values
    and returns the average of that window.
    """
    def __init__(self, size=5):
        self.buffer = []
        self.size = size

    def filter(self, new_value):
        self.buffer.append(new_value)
        if len(self.buffer) > self.size:
            self.buffer.pop(0)
        return sum(self.buffer) / len(self.buffer)


class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')
        self.subscription = self.create_subscription(
            TwistStamped,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        self.subscription  # prevent unused variable warning

        self.odom_publisher = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.motor_init()

        # Robot state
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()
        self.last_encoder_left = 0.0
        self.last_encoder_right = 0.0

        # Encoder parameters (adjust for your robot)
        self.track_width = 0.15       # Distance between tracks (meters)
        self.track_radius = 0.025     # Effective track radius (meters)
        self.encoder_resolution = 1000  # Pulses per revolution

        # 3) Filters for Encoder Data
        # - First pass each reading through a Median Filter
        # - Then pass the result through a Moving Average Filter
        self.median_left = MedianFilter(size=5)
        self.median_right = MedianFilter(size=5)
        self.average_left = MovingAverageFilter(size=6)
        self.average_right = MovingAverageFilter(size=6)

        # Timer to update odometry at ~30 Hz
        self.timer = self.create_timer(0.3, self.update_odometry)

    def motor_init(self):
        self.get_logger().info("Initializing motor...")
        try:
            bus.write_byte_data(MOTOR_ADDR, MOTOR_TYPE_ADDR, MotorType)
            time.sleep(0.5)
            bus.write_byte_data(MOTOR_ADDR, MOTOR_ENCODER_POLARITY_ADDR, MotorEncoderPolarity)
            self.get_logger().info("Motor initialized.")
        except OSError as e:
            self.get_logger().error(f"Failed to initialize motor: {e}")

    def cmd_vel_callback(self, msg):
        try:
            # Extract linear and angular velocities from the Twist message
            linear_x = msg.twist.linear.x
            angular_z = msg.twist.angular.z

            # Translate velocities to motor speeds
            left_speed = int((linear_x - angular_z) * 50)
            right_speed = int((linear_x + angular_z) * 50)

            # Ensure speeds are within valid range
            left_speed = max(min(left_speed, 100), -100)
            right_speed = max(min(right_speed, 100), -100)

            # Send motor speed commands via I2C
            speed_command = [right_speed, left_speed]
            bus.write_i2c_block_data(MOTOR_ADDR, MOTOR_FIXED_SPEED_ADDR, speed_command)
        except Exception as e:
            self.get_logger().error(f"Error in cmd_vel_callback: {e}")

    def update_odometry(self):
        try:
            current_time = self.get_clock().now()
            dt = (current_time - self.last_time).nanoseconds / 1e9  # Seconds

            # Read encoder values (with simple retry logic)
            encoder_data = None
            for _ in range(3):
                try:
                    raw_data = bus.read_i2c_block_data(MOTOR_ADDR, MOTOR_ENCODER_TOTAL_ADDR, 8)
                    encoder_data = struct.unpack('ii', bytes(raw_data))
                    break
                except OSError as e:
                    self.get_logger().warn(f"Failed to read encoder data, retrying...: {e}")
                    time.sleep(0.1)

            if encoder_data is None:
                self.get_logger().error("Failed to read encoder data after retries.")
                return

            raw_left = encoder_data[0]
            raw_right = encoder_data[1]

            # 1) Median Filter
            med_left = self.median_left.filter(raw_left)
            med_right = self.median_right.filter(raw_right)

            # 2) Moving Average Filter
            enc_left = self.average_left.filter(med_left)
            enc_right = self.average_right.filter(med_right)

            # Calculate deltas
            delta_left = enc_left - self.last_encoder_left
            delta_right = enc_right - self.last_encoder_right

            # Store for next iteration
            self.last_encoder_left = enc_left
            self.last_encoder_right = enc_right

            # Convert pulses to distance
            distance_left = (delta_left / self.encoder_resolution) * (2 * 3.14159 * self.track_radius)
            distance_right = (delta_right / self.encoder_resolution) * (2 * 3.14159 * self.track_radius)

            # Compute linear and angular velocity
            v_left = distance_left / dt
            v_right = distance_right / dt
            v = (v_left + v_right) / 2.0
            omega = (v_right - v_left) / self.track_width

            # Update robot pose
            self.x += v * dt * cos(self.theta)
            self.y += v * dt * sin(self.theta)
            self.theta += omega * dt

            # Normalize theta to [-pi, pi]
            self.theta = (self.theta + 3.14159) % (2 * 3.14159) - 3.14159

            # Create quaternion from yaw
            odom_quat = tf_transformations.quaternion_from_euler(0, 0, self.theta)

            # Build odometry message
            odom_msg = Odometry()
            odom_msg.header.stamp = current_time.to_msg()
            odom_msg.header.frame_id = 'odom'
            odom_msg.child_frame_id = 'base_link'

            # Pose
            odom_msg.pose.pose.position.x = self.x
            odom_msg.pose.pose.position.y = self.y
            odom_msg.pose.pose.orientation.x = odom_quat[0]
            odom_msg.pose.pose.orientation.y = odom_quat[1]
            odom_msg.pose.pose.orientation.z = odom_quat[2]
            odom_msg.pose.pose.orientation.w = odom_quat[3]

            # Covariance for Pose (example: small uncertainty in x, y, large in z, etc.)
            # Typically for 2D differential drive, z is "unobserved" so set it high
            # x, y, theta might have small but nonzero covariances
            odom_msg.pose.covariance = [
                0.001, 0,     0,     0,     0,     0,
                0,     0.001, 0,     0,     0,     0,
                0,     0,     99999, 0,     0,     0,
                0,     0,     0,     99999, 0,     0,
                0,     0,     0,     0,     99999, 0,
                0,     0,     0,     0,     0,     0.01
            ]

            # Twist
            odom_msg.twist.twist.linear.x = v
            odom_msg.twist.twist.linear.y = 0.0
            odom_msg.twist.twist.angular.z = omega

            # Covariance for Twist
            odom_msg.twist.covariance = [
                0.001, 0,     0,     0,     0,     0,
                0,     0.001, 0,     0,     0,     0,
                0,     0,     99999, 0,     0,     0,
                0,     0,     0,     99999, 0,     0,
                0,     0,     0,     0,     99999, 0,
                0,     0,     0,     0,     0,     0.01
            ]

            # Publish odometry
            self.odom_publisher.publish(odom_msg)

            # Publish TF transform
            t = TransformStamped()
            t.header.stamp = current_time.to_msg()
            t.header.frame_id = 'odom'
            t.child_frame_id = 'base_link'
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation.x = odom_quat[0]
            t.transform.rotation.y = odom_quat[1]
            t.transform.rotation.z = odom_quat[2]
            t.transform.rotation.w = odom_quat[3]
            self.tf_broadcaster.sendTransform(t)

            self.last_time = current_time

        except Exception as e:
            self.get_logger().error(f"Error in update_odometry: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = MotorController()
    node.get_logger().info("MotorController node has been initialized.")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down MotorController node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
