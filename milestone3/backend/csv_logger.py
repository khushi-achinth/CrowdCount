import csv
import os
import time

os.makedirs("logs", exist_ok=True)
FILE = "logs/crowd_data.csv"

_buffer = []
_last_flush = time.time()

if not os.path.exists(FILE):
    with open(FILE, "w", newline="") as f:
        csv.writer(f).writerow(["time", "zone", "count"])

def log(zone, count):
    global _last_flush
    _buffer.append([time.strftime("%H:%M:%S"), zone, count])

    # flush every 5 seconds
    if time.time() - _last_flush >= 5:
        with open(FILE, "a", newline="") as f:
            csv.writer(f).writerows(_buffer)
        _buffer.clear()
        _last_flush = time.time()
