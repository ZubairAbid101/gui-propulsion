import time
import RPi.GPIO as GPIO
from hx711 import HX711

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Initialize HX711 for one load cell
hx1 = HX711(dout_pin=5, pd_sck_pin=6)

hx1.zero()

# Calibration factor (adjust based on calibration)
calibration_factor_1 = 42.0
hx1.set_scale_ratio(calibration_factor_1)

# Filtering parameters
EMA_ALPHA = 0.2  # Exponential Moving Average smoothing factor

# Filtered and stable weights
filtered_weight_1 = None
stable_weight_1 = None

def filter_reading(new_weight, filtered):
    """Apply Exponential Moving Average (EMA) filter."""
    if filtered is None:
        return new_weight
    return EMA_ALPHA * new_weight + (1 - EMA_ALPHA) * filtered

def is_outlier(new_weight, stable):
    """Detect outliers in both directions (spikes up or down)."""
    if stable is None:
        return False
    change = abs(new_weight - stable)
    threshold = max(15, 0.15 * abs(stable))
    return change >= threshold

def read_load_cells():
    global filtered_weight_1, stable_weight_1

    raw1 = hx1.get_weight_mean(readings=5)
    if raw1 is False:  # Handle invalid readings
        return {
            "Load Cell 1 (Raw)": 0.0,
            "Load Cell 1 (Filtered)": 0.0,
            "Load Cell 1 (Stable)": 0.0,
        }
    
    # Apply filtering
    filtered_weight_1 = filter_reading(raw1, filtered_weight_1)

    # Update stable weight if not outlier
    if not is_outlier(filtered_weight_1, stable_weight_1):
        if stable_weight_1 is None or abs(filtered_weight_1 - stable_weight_1) < 5:
            stable_weight_1 = filtered_weight_1

    return {
        "Load Cell 1 (Raw)": round(raw1, 2),
        "Load Cell 1 (Filtered)": round(filtered_weight_1, 2) if filtered_weight_1 else 0.0,
        "Load Cell 1 (Stable)": round(stable_weight_1, 2) if stable_weight_1 else 0.0,
    }

# Example usage loop
if __name__ == "__main__":
    try:
        while True:
            print(read_load_cells())
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
