import smbus2
import time

# Use I2C bus 3
bus = smbus2.SMBus(3)
address = 0x5A  # MLX90614 default address

try:
    # Read object temperature (register 0x07)
    raw_data = bus.read_word_data(address, 0x07)
    temp = (raw_data * 0.02) - 273.15  # Convert to Celsius
    print(f"Object Temperature: {temp:.2f} °C")
except Exception as e:
    print(f"Error: {e}")
finally:
    bus.close()
