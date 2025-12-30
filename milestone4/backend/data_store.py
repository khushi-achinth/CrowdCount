import time
import json
import os
from csv_logger import log_row
from config import get_thresholds, WARNING_OFFSET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONES_FILE = os.path.join(BASE_DIR, "detector/zones.json")

# Load zone order ONCE (authoritative)
with open(ZONES_FILE, "r") as f:
    ZONE_ORDER = [z["name"] for z in json.load(f)["zones"]]

data = {
    "zones": {},
    "time": []
}

CSV_INTERVAL = 1
_last_csv_time = 0


def update(zone, count):
    global _last_csv_time

    thresholds = get_thresholds()
    threshold = thresholds.get(zone, 20)

    # ---- INIT ZONE IF NEW ----
    if zone not in data["zones"]:
        data["zones"][zone] = {
            "count": 0,
            "history": [],
            "threshold": threshold,   # ✅ CORRECTLY ATTACHED
            "alert": ""
        }

    # ---- UPDATE COUNT ----
    data["zones"][zone]["count"] = count
    data["zones"][zone]["history"].append(count)
    data["time"].append(time.strftime("%H:%M:%S"))

    # ---- ALERT LOGIC (UNCHANGED SEMANTICS) ----
    if count >= threshold:
        data["zones"][zone]["alert"] = "Overcrowded"
    elif count >= threshold - WARNING_OFFSET:
        data["zones"][zone]["alert"] = "Approaching capacity"
    else:
        data["zones"][zone]["alert"] = ""

    # ---- CSV LOGGING (ORDERED + SAFE) ----
    now = time.time()
    if now - _last_csv_time >= CSV_INTERVAL:
        _last_csv_time = now

        ordered_counts = [
            data["zones"].get(z, {"count": 0})["count"]
            for z in ZONE_ORDER
        ]

        log_row(time.strftime("%H:%M:%S"), *ordered_counts)
