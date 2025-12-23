import csv
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
CSV_FILE = os.path.join(LOG_DIR, "crowd_data.csv")

HEADER = ["Time", "Entrance", "Walk Path", "Exit", "Total"]

os.makedirs(LOG_DIR, exist_ok=True)

def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)

def log_row(time_str, entrance, walkpath, exit_):
    ensure_csv()
    total = entrance + walkpath + exit_
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([time_str, entrance, walkpath, exit_, total])
