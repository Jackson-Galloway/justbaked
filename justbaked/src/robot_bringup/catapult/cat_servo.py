import RPi.GPIO as GPIO
import time

# Set up the GPIO mode (BCM)
GPIO.setmode(GPIO.BCM)

# Set the pin for servo control (GPIO5) (Pin 29)
servo_pin = 5

# Set the servo pin as an output
GPIO.setup(servo_pin, GPIO.OUT)

# Create a PWM instance (50Hz)
pwm = GPIO.PWM(servo_pin, 50)

# Start PWM with a 0% duty cycle
pwm.start(0)

try:
    # Move the servo to 0 degrees (duty cycle around 5%)
    pwm.ChangeDutyCycle(5)
    time.sleep(1)

    # Move the servo to 90 degrees (duty cycle around 7.5%)
    pwm.ChangeDutyCycle(7.5)
    time.sleep(1)

    # Move the servo to 180 degrees (duty cycle around 10%)
    pwm.ChangeDutyCycle(10)
    time.sleep(1)

except KeyboardInterrupt:
    pass

# Stop PWM and clean up the GPIO
pwm.stop()
GPIO.cleanup()
