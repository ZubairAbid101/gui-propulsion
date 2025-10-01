import time
import board, busio
import adafruit_mlx90614

# ——— I2C setup ———
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
mlx = adafruit_mlx90614.MLX90614(i2c)

def read_temp():
    """Reads object temperature from the MLX90614 sensor."""
    target_temp = float(f"{mlx.object_temperature:.2f}")
    return {'target_temp': target_temp}
