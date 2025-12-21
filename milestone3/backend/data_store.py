import time
from backend.config import THRESHOLDS, WARNING_OFFSET
from backend.csv_logger import log_row

# ---------------- IN-MEMORY LIVE DATA ----------------

data = {
    "zones": {
        "entrance": {"count": 0, "history": [], "alert": ""},
        "retail": {"count": 0, "history": [], "alert": ""},
        "foodcourt": {"count": 0, "history": [], "alert": ""}
    },
    "time": []
}

# ---------------- CSV LOGGING CONTROL ----------------

CSV_INTERVAL = 4  # seconds
_last_csv_time = 0


def update(zone, count):
    global _last_csv_time

    # Update live zone data (EVERY UPDATE)
    data["zones"][zone]["count"] = count
    data["zones"][zone]["history"].append(count)
    data["time"].append(time.strftime("%H:%M:%S"))

    # -------- ALERT LOGIC --------
    threshold = THRESHOLDS[zone]

    if count >= threshold:
        data["zones"][zone]["alert"] = f"{zone.capitalize()} is overcrowded"
    elif count >= threshold - WARNING_OFFSET:
        data["zones"][zone]["alert"] = f"{zone.capitalize()} capacity approaching"
    else:
        data["zones"][zone]["alert"] = ""

    # -------- CSV LOGGING (EVERY 5 SECONDS) --------
    now = time.time()
    if now - _last_csv_time >= CSV_INTERVAL:
        _last_csv_time = now

        entrance = data["zones"]["entrance"]["count"]
        retail = data["zones"]["retail"]["count"]
        foodcourt = data["zones"]["foodcourt"]["count"]

        log_row(
            time.strftime("%H:%M:%S"),
            entrance,
            retail,
            foodcourt
        )
