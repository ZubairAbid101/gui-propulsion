import time
import pigpio  # For precise PWM control
import sys
import subprocess

# Start the pigpio daemon
subprocess.run(["sudo", "systemctl", "start", "pigpiod"])
# Define GPIO pins for the servos
SERVO1_PIN = 18  # Main servo
SERVO2_PIN = 23  # Choke control servo

# Initialize pigpio
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon.")
    sys.exit(1)

# Servo pulse width range (Standard: 500 - 2500 µs, Typical: 1000 - 2000 µs)
SERVO_MIN_PW = 500   # Minimum pulse width (0°)
SERVO_MAX_PW = 2500  # Maximum pulse width (180°)

# Function to set servo angle
def set_servo_angle(servo_pin, angle):
    """Convert angle (0-180) to PWM pulse width (500-2500 µs)"""
    pulse_width = int(SERVO_MIN_PW + (angle / 180) * (SERVO_MAX_PW - SERVO_MIN_PW))
    pi.set_servo_pulsewidth(servo_pin, pulse_width)
    print(f"Servo on GPIO {servo_pin} set to {angle}°")

# Function to control the choke (open or close)
def toggle_choke(is_open):
    """Open or close the choke based on the provided state."""
    if is_open:
        set_servo_angle(SERVO1_PIN, 90)  # Choke open position
        print("Choke opened.")
    else:
        set_servo_angle(SERVO1_PIN, 0)  # Choke closed position
        print("Choke closed.")