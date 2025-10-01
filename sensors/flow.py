import time
import RPi.GPIO as GPIO
from hx711 import HX711

# Configuration
EMA_ALPHA = 0.2
OUTLIER_MIN = 15            # grams
OUTLIER_REL = 0.15          # 15%
DENSITY = 871               # g/L
INTERVAL = 1                # seconds
READINGS = 5                # samples per read

# Internal state
_filtered_weight = None
_stable_weight = None
_interval_start_time = None
_interval_start_weight = None

# Initialize GPIO and scale once
GPIO.setmode(GPIO.BCM)
hx = HX711(dout_pin=21, pd_sck_pin=20)
hx.zero()
hx.set_scale_ratio(40)

# Helpers
def _filter_reading(new):
    global _filtered_weight
    _filtered_weight = new if _filtered_weight is None else EMA_ALPHA * new + (1 - EMA_ALPHA) * _filtered_weight
    return _filtered_weight

def _is_outlier(new):
    global _stable_weight
    if _stable_weight is None:
        return False
    change = abs(new - _stable_weight)
    threshold = max(OUTLIER_MIN, OUTLIER_REL * abs(_stable_weight))
    return change >= threshold

# Public API for GUI
def read_flow():
    """
    Perform one weight-reading cycle and return a dict with:
      - raw_weight
      - current_weight (EMA-filtered)
      - stable_weight
      - grams_per_min
      - liters_per_min
    """
    global _stable_weight, _interval_start_time, _interval_start_weight

    raw = hx.get_weight_mean(readings=READINGS)
    if raw is False:
        return {
            'raw_weight': None,
            'current_weight': None,
            'stable_weight': _stable_weight,
            'grams_per_min': 'No Raw Data',
            'liters_per_min': 'No Raw Data'
        }

    w = _filter_reading(raw)
 
    '''
    if _is_outlier(w):
        # Ignore outlier, keep last stable values
        return {
            'raw_weight': raw,
            'current_weight': w,
            'stable_weight': _stable_weight,
            'grams_per_min': 'Is Outlier',
            'liters_per_min': 'Is Outlier'
        }
    '''
    
    # update stable weight
    if _stable_weight is None or abs(w - _stable_weight) < 5:
        _stable_weight = w

    # init interval
    if _interval_start_time is None:
        _interval_start_time = time.time()
        _interval_start_weight = w

    data = {
        'raw_weight': raw,
        'current_weight': w,
        'stable_weight': _stable_weight,
        'grams_per_min': 0,
        'liters_per_min': 0
    }

    # interval check
    if time.time() - _interval_start_time >= INTERVAL:
        delta = _interval_start_weight - w  # positive = fuel leaving
        gpm = max(0, delta * (60 / INTERVAL))  # clamp to zero
        #gpm = delta * (60 / INTERVAL)  # clamp to zero
        lpm = gpm / DENSITY
        data['grams_per_min'] = round(gpm, 2)
        data['liters_per_min'] = round(lpm, 4)
        # reset interval
        _interval_start_time = time.time()
        _interval_start_weight = w

    return data


# Standalone test runner
if __name__ == '__main__':
    try:
        while True:
            reading = read_flow()
            print(reading)
            time.sleep(1)  # adjust sampling speed
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
