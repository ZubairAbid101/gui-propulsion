from gpiozero import Button
import time

# CONFIG
TACH_PIN = 17       # GPIO pin number
PPR = 1             # Pulses per revolution

# Setup
hall = Button(TACH_PIN)
pulse_count = 0

def count_pulse():
    global pulse_count
    pulse_count += 1

hall.when_pressed = count_pulse

def read_rpm(duration=1):
    """
    Measure RPM over a given duration (seconds).
    Returns a dict: {"rpm": value, "pulses": value}
    """
    global pulse_count
    pulse_count = 0
    time.sleep(duration)
    rpm = (pulse_count / PPR) * (60 / duration)
    return {"rpm": round(rpm, 2), "pulses": pulse_count}
