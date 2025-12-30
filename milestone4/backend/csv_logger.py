import csv
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
CSV_FILE = os.path.join(LOG_DIR, "crowd_data.csv")
ZONES_FILE = os.path.join(BASE_DIR, "detector/zones.json")

os.makedirs(LOG_DIR, exist_ok=True)


def get_zone_names():
    with open(ZONES_FILE, "r") as f:
        return [z["name"] for z in json.load(f)["zones"]]


def ensure_csv():
    if os.path.exists(CSV_FILE):
        return

    zones = get_zone_names()
    header = ["Timestamp"] + zones + ["Total"]

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)


def log_row(timestamp, *counts):
    ensure_csv()
    total = sum(counts)

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, *counts, total])
