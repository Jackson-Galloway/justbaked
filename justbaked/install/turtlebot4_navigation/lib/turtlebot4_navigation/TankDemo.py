import smbus
import time
import struct
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# (Set the I2C bus number, usually 1)
I2C_BUS = 1

# (Set the I2C address of the 4-ch encoder motor driver)
MOTOR_ADDR = 0x34 

# (Register address)
ADC_BAT_ADDR = 0x00
MOTOR_TYPE_ADDR = 0x14 #Set the encoder motor type
MOTOR_ENCODER_POLARITY_ADDR = 0x15 #Set the polarity of the encoder)，
#If the motor speed can not be controlled, either rotating at the fastest speed or stopping, the value of this address can be reset
#Range: 0 or 1, default: 0)
MOTOR_FIXED_PWM_ADDR = 0x1F #-100~100）(Fixed PWM control, open-loop control, range: (-100~100))  
MOTOR_FIXED_SPEED_ADDR = 0x33 #Fixed speed control, closed-loop control,)，
#(Unit: pulse count per 10 milliseconds, range: (depending on the specific encoder motor, affected by the number of encoder wires, voltage, load, etc., generally around ±50))

MOTOR_ENCODER_TOTAL_ADDR = 0x3C #Total pulse value of each of the four encoder motors
# If the number of pulses per revolution of the motor is known as U, and the diameter of the wheel is known as D, the distance traveled by each wheel can be obtained by counting the pulses)
# (P/U) * (3.14159*D)(For example, if the total number of pulses for motor 1 is P, the distance traveled is (P/U) * (3.14159*D))
# The number of pulses per revolution U for different motors can be tested manually by rotating 10 revolutions and reading the pulse count, and then taking the average value to obtain)


#(Motor type values)
MOTOR_TYPE_JGB37_520_12V_110RPM = 3 #Magnetic ring rotates 44 pulses per revolution, reduction ratio: 90, default
ro#(Motor type and encoder direction polarity)
MotorType = MOTOR_TYPE_JGB37_520_12V_110RPM
MotorEncoderPolarity = 0

bus = smbus.SMBus(I2C_BUS)

class MotorController(Node):
    def __init__(self):
        super().__init__('motor_controller')
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.motor_init()

    def motor_init(self):
        bus.write_byte_data(MOTOR_ADDR, MOTOR_TYPE_ADDR, MotorType)  # Set the motor type
        time.sleep(0.5)
        bus.write_byte_data(MOTOR_ADDR, MOTOR_ENCODER_POLARITY_ADDR, MotorEncoderPolarity)  # Set the polarity of the encoder

    def cmd_vel_callback(self, msg):
        # Extract linear and angular velocities from the Twist message
        linear_x = msg.linear.x
        angular_z = msg.angular.z

        # Translate velocities to motor speeds
        left_speed = int((linear_x - angular_z) * 50)  # Adjust the scaling factor as needed
        right_speed = int((linear_x + angular_z) * 50)  # Adjust the scaling factor as needed

        # Ensure the speeds are within the valid range
        left_speed = max(min(left_speed, 100), -100)
        right_speed = max(min(right_speed, 100), -100)

        # Send motor speed commands via I2C
        speed_command = [left_speed, left_speed, right_speed, right_speed]
        bus.write_i2c_block_data(MOTOR_ADDR, MOTOR_FIXED_SPEED_ADDR, speed_command)

def main(args=None):
    rclpy.init(args=args)
    motor_controller = MotorController()
    rclpy.spin(motor_controller)
    motor_controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()



