import time
from csv_logger import log_row
from config import THRESHOLDS, WARNING_OFFSET

data = {
    "zones": {
        "entrance": {"count": 0, "history": [], "alert": ""},
        "walkpath": {"count": 0, "history": [], "alert": ""},
        "exit": {"count": 0, "history": [], "alert": ""}
    },
    "time": []
}

CSV_INTERVAL = 1  # seconds
_last_csv_time = 0

def update(zone, count):
    global _last_csv_time

    data["zones"][zone]["count"] = count
    data["zones"][zone]["history"].append(count)
    data["time"].append(time.strftime("%H:%M:%S"))

    threshold = THRESHOLDS[zone]

    if count >= threshold:
        data["zones"][zone]["alert"] = "Overcrowded"
    elif count >= threshold - WARNING_OFFSET:
        data["zones"][zone]["alert"] = "Approaching capacity"
    else:
        data["zones"][zone]["alert"] = ""

    now = time.time()
    if now - _last_csv_time >= CSV_INTERVAL:
        _last_csv_time = now
        log_row(
            time.strftime("%H:%M:%S"),
            data["zones"]["entrance"]["count"],
            data["zones"]["walkpath"]["count"],
            data["zones"]["exit"]["count"]
        )
