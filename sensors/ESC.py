import time
import pigpio  # For precise PWM control
import sys
import subprocess

# Start the pigpio daemon
subprocess.run(["sudo", "systemctl", "start", "pigpiod"])

# Define ESC pin (Change this if needed)
ESC_PIN = 12  # GPIO pin connected to ESC signal wire

# Initialize pigpio
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio daemon.")
    sys.exit(1)

# Variables
THROTTLE_CUT = True  # Flag to indicate if throttle is cut

# Function to set throttle percentage (0 to 100)
def set_throttle(throttle_percent):
    pulse_width = int((throttle_percent / 100) * 1000) + 1000  # Map to 1000–2000 µs
    pi.set_servo_pulsewidth(ESC_PIN, pulse_width)
    #print_with_timestamp(f"Throttle set to {throttle_percent}%")

# Function to print messages with timestamps
def print_with_timestamp(message):
    timestamp = int(time.time() * 1000)
    print(f"[{timestamp} ms] {message}")

# Setup ESC
#print_with_timestamp("Initializing ESC...")
set_throttle(0)  # Start at 0% throttle
time.sleep(2)  # Allow ESC to initialize

# Now we are not taking user input here, it's controlled by the GUI
def cut_throttle():
    """Cut the throttle (set to 0)."""
    set_throttle(0)
    global THROTTLE_CUT
    THROTTLE_CUT = True
    #print_with_timestamp("Throttle cut to 0%!")

def restart_throttle():
    """Restart the throttle (set to 100)."""
    global THROTTLE_CUT
    if THROTTLE_CUT:
        set_throttle(100)
        THROTTLE_CUT = False
        #print_with_timestamp("Throttle restarted to 100%!")
    #else:
        #print_with_timestamp("Throttle is already running. No action taken.")
