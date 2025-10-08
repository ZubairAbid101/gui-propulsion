import time
import RPi.GPIO as GPIO
from hx711 import HX711

# GPIO setup
GPIO.setmode(GPIO.BCM)

# Initialize HX711 for one load cell
hx1 = HX711(dout_pin=5, pd_sck_pin=6)
hx2 = HX711(dout_pin=13, pd_sck_pin=19)

hx1.zero()
hx2.zero()

# Calibration factor (adjust based on calibration)
calibration_factor_1 = 42.0
calibration_factor_2 = 42.0
hx1.set_scale_ratio(calibration_factor_1)
hx2.set_scale_ratio(calibration_factor_2)

# Filtering parameters
EMA_ALPHA = 0.2  # Exponential Moving Average smoothing factor

# Filtered and stable weights
filtered_weight_1 = None
stable_weight_1 = None

filtered_weight_2 = None
stable_weight_2 = None

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
    global filtered_weight_1, stable_weight_1, filtered_weight_2, stable_weight_2

    # --- Load Cell 1 ---
    raw1 = hx1.get_weight_mean(readings=5)
    if raw1 is not False:
        filtered_weight_1 = filter_reading(raw1, filtered_weight_1)
        if not is_outlier(filtered_weight_1, stable_weight_1):
            if stable_weight_1 is None or abs(filtered_weight_1 - stable_weight_1) < 5:
                stable_weight_1 = filtered_weight_1
    else:
        raw1, filtered_weight_1, stable_weight_1 = 0.0, 0.0, 0.0

    # --- Load Cell 2 ---
    raw2 = hx2.get_weight_mean(readings=5)
    if raw2 is not False:
        filtered_weight_2 = filter_reading(raw2, filtered_weight_2)
        if not is_outlier(filtered_weight_2, stable_weight_2):
            if stable_weight_2 is None or abs(filtered_weight_2 - stable_weight_2) < 5:
                stable_weight_2 = filtered_weight_2
    else:
        raw2, filtered_weight_2, stable_weight_2 = 0.0, 0.0, 0.0

    return {
        # Load Cell 1
        "Load Cell 1 (Raw)": round(raw1, 2),
        "Load Cell 1 (Filtered)": round(filtered_weight_1, 2) if filtered_weight_1 else 0.0,
        "Load Cell 1 (Stable)": round(stable_weight_1, 2) if stable_weight_1 else 0.0,
        
        # Load Cell 2
        "Load Cell 2 (Raw)": round(raw2, 2),
        "Load Cell 2 (Filtered)": round(filtered_weight_2, 2) if filtered_weight_2 else 0.0,
        "Load Cell 2 (Stable)": round(stable_weight_2, 2) if stable_weight_2 else 0.0,
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
