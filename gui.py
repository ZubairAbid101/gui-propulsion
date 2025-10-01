# Importing Packages
import numpy as np
import pandas as pd
from collections import deque
import threading
import queue
import time
import random
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb

# Sensor Imports
#from sensors.ESC import cut_throttle, restart_throttle
#from sensors.servos import set_servo_angle, toggle_choke
#from sensors.temp import read_temp
#from sensors.rpm import read_rpm
#from sensors.load_cell import read_load_cells
#from sensors.flow import read_flow

# Read all sensor values (mock implementation)
def read_sensors():
    sensor_values = {
        # Temperature between 15°C and 100°C
        "Temperature": round(random.uniform(15, 100), 2),

        # RPM between 0 and 6000 rpm
        "RPM": random.randint(0, 6000),

        # Load cells produce forces, say between -1000 and 1000 N
        "Load Cell 1": round(random.uniform(-1000, 1000), 2),
        "Load Cell 2": round(random.uniform(-1000, 1000), 2),

        # Flow sensors: 0–2000 g/min and 0–20 L/min
        "grams_per_min": round(random.uniform(0, 2000), 2),
        "liters_per_min": round(random.uniform(0, 20), 2)
    }
    return sensor_values

class SensorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Raspberry Pi Sensor Dashboard")

        # Configure main grid
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=3)
        root.rowconfigure(0, weight=1)

        # Frames
        self.frame_controls = ttk.Frame(root, padding=10)
        self.frame_sensors = ttk.Frame(root, padding=10)

        self.frame_controls.grid(row=0, column=0, sticky="nsew")
        self.frame_sensors .grid(row=0, column=1, sticky="nsew")

        # Control layout weights
        self.frame_controls.columnconfigure(0, weight=1)
        for r in range(6):
            self.frame_controls.rowconfigure(r, weight=1)

        # Status Label
        self.status_label = ttk.Label(
            self.frame_controls, text="", width=50, anchor="center", justify="center")
        self.status_label.grid(row=0, column=0, sticky="ew", pady=5)

        # Throttle Slider
        self.throttle_var = tk.DoubleVar(value=90)
        self.throttle_slider = ttk.Scale(
            self.frame_controls, from_=40, to=120,
            orient=tk.HORIZONTAL, variable=self.throttle_var,
            command=self.on_throttle_change)
        self.throttle_slider.grid(row=1, column=0, sticky="ew", pady=5)
        self.throttle_label = ttk.Label(
            self.frame_controls, text="Throttle: 90°")
        self.throttle_label.grid(row=2, column=0, pady=5)
        self.update_servo_angle()

        # Increment/Decrement
        self.button_frame = ttk.Frame(self.frame_controls)
        self.button_frame.grid(row=3, column=0, pady=5)
        self.decrement_button = ttk.Button(
            self.button_frame, text="➖", command=self.decrement_throttle)
        self.decrement_button.pack(side=tk.LEFT, padx=5)
        self.increment_button = ttk.Button(
            self.button_frame, text="➕", command=self.increment_throttle)
        self.increment_button.pack(side=tk.LEFT, padx=5)

        # Choke & Cut/Restart
        self.choke_state = tk.BooleanVar(value=False)
        self.choke_button = ttk.Button(
            self.frame_controls, text="Choke: Closed", width=20, command=self.toggle_choke)
        self.choke_button.grid(row=4, column=0, pady=5)
        self.sensor_active = True
        self.cut_restart_button = ttk.Button(
            self.frame_controls, text="State: Cut", width=20, command=self.toggle_cut_restart)
        self.cut_restart_button.grid(row=5, column=0, pady=5)

        # ------------------- Sensor Display -------------------
        self.frame_sensors.columnconfigure((0, 1), weight=1)
        self.frame_sensors.rowconfigure((0, 1), weight=1)
        self.sensor_labels = {}
        self.avg_labels = {}
        self.create_sensor_display()

        # Data storage
        self.sensor_data = {
            "Temperature": deque(maxlen=20),
            "RPM": deque(maxlen=20),
            "Load Cell 1": deque(maxlen=20),
            "Load Cell 2": deque(maxlen=20),
            'grams_per_min': deque(maxlen=20),
            'liters_per_min': deque(maxlen=20)
        }
        self.avg_data = {
            "Temperature": deque(maxlen=20),
            "RPM": deque(maxlen=20),
            "Load Cell 1": deque(maxlen=20),
            "Load Cell 2": deque(maxlen=20),
            "grams_per_min": deque(maxlen=20),
            "liters_per_min": deque(maxlen=20)
        }

        self.moving_avg_window = 5
        self.wait_time_after_choke = 5
        self.after_delay = 1000  # ms
        self.waiting_for_readings = 0
        self._excel_buffer = []

        self.root.after(0, self.poll_sensors)

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def poll_sensors(self):
        if self.choke_state.get():
            if self.waiting_for_readings > 0:
                self.waiting_for_readings -= 1
                self.status_label.config(
                    text=f"Waiting for {self.waiting_for_readings} cycles before resuming...")
            else:
                values = read_sensors()
                if not values or any(v is None for v in values.values()):
                    self.status_label.config(
                        text="Sensor missing, skipping cycle...")
                    self.waiting_for_readings = self.wait_time_after_choke
                else:
                    excel_values = values.copy()
                    excel_values['Throttle'] = int(self.throttle_var.get())
                    self._excel_buffer.append(excel_values)
                    self._update_values(values)
                    self.status_label.config(text="")

        self.root.after(self.after_delay, self.poll_sensors)

    def _update_values(self, sensor_values):
        for key, value in sensor_values.items():
            self.sensor_labels[key].config(text=f"{value: 0.3f}")
            self.sensor_data[key].append(value)

            avg_value = np.mean(
                list(self.sensor_data[key])[-self.moving_avg_window:])
            self.avg_data[key].append(avg_value)
            self.avg_labels[key].config(text=f"Avg: {avg_value:.3f}")

    def increment_throttle(self):
        new_value = min(120, self.throttle_var.get() + 1)
        self.throttle_var.set(new_value)
        self.throttle_label.config(text=f"Throttle: {int(new_value)}°")
        self.on_throttle_change()

    def decrement_throttle(self):
        new_value = max(0, self.throttle_var.get() - 1)
        self.throttle_var.set(new_value)
        self.throttle_label.config(text=f"Throttle: {int(new_value)}°")
        self.on_throttle_change()

    def create_sensor_display(self):
        sensors = ["Temperature", "RPM", "Load Cell 1",
                   "Load Cell 2", "grams_per_min", "liters_per_min"]
        for idx, sensor in enumerate(sensors):
            row, col = divmod(idx, 2)

            container = ttk.LabelFrame(self.frame_sensors, text=sensor)
            container.grid(row=row, column=col, padx=10,
                           pady=10, sticky="nsew")
            container.grid_propagate(False)
            container.configure(width=220, height=130)

            inner_frame = ttk.Frame(container)
            inner_frame.place(relx=0.5, rely=0.5, anchor="center")

            label = ttk.Label(inner_frame, text="0", font=("Arial", 20))
            label.pack(anchor="center")

            avg_label = ttk.Label(inner_frame, text="Avg: 0", font=(
                "Arial", 18), foreground="gray")
            avg_label.pack(anchor="center")

            self.sensor_labels[sensor] = label
            self.avg_labels[sensor] = avg_label

    def toggle_choke(self):
        self.choke_state.set(not self.choke_state.get())
        if self.choke_state.get():
            self.choke_button.config(text="Choke: Open")
            self.waiting_for_readings = self.wait_time_after_choke
        else:
            self.choke_button.config(text="Choke: Closed")
            self.clear_data()
            self.status_label.config(text="Choke Closed: Data Cleared")

    def toggle_cut_restart(self):
        if self.sensor_active:
            self.sensor_active = False
            #restart_throttle()
            self.clear_data()
            self.cut_restart_button.config(text="Restart")
        else:
            self.sensor_active = True
            #cut_throttle()
            self.cut_restart_button.config(text="Cut")

    def clear_data(self):
        for key in self.sensor_data:
            self.sensor_data[key].clear()
            self.avg_data[key].clear()
            self.sensor_labels[key].config(text="0")
            self.avg_labels[key].config(text="Avg: 0")

    def on_throttle_change(self, event=None):
        throttle_value = int(self.throttle_var.get())
        self.throttle_label.config(text=f"Throttle: {throttle_value}°")
        self.update_servo_angle(throttle_value)

        self.clear_data()

    def update_servo_angle(self, angle=None):
        if angle is None:
            angle = int(self.throttle_var.get())

        #set_servo_angle(18, angle)

    def on_close(self):
        if self._excel_buffer:
            df = pd.DataFrame(self._excel_buffer)
            with pd.ExcelWriter("sensor_readings.xlsx", engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Readings")
            print(f"Saved {len(df)} readings to sensor_readings.xlsx")

        self.root.quit()
        self.root.destroy()

# Run Application
if __name__ == "__main__":
    root = tb.Window(themename="superhero")
    app = SensorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
