import time, json, os
from csv_logger import log_row

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONE_CONFIG = os.path.join(BASE_DIR, "backend", "zone_config.json")

data = {
    "zones": {},
    "time": []
}

def load_config():
    with open(ZONE_CONFIG, "r") as f:
        return json.load(f)

def update(zone_id, count):
    zone_id = str(zone_id)
    cfg = load_config()

    if zone_id not in data["zones"]:
        data["zones"][zone_id] = {
            "count": 0,
            "history": [],
            "alert": ""
        }

    data["zones"][zone_id]["count"] = count
    data["zones"][zone_id]["history"].append(count)
    data["time"].append(time.strftime("%H:%M:%S"))

    threshold = cfg[zone_id]["threshold"]
    if count >= threshold:
        data["zones"][zone_id]["alert"] = "Overcrowded"
    elif count >= threshold - 2:
        data["zones"][zone_id]["alert"] = "Approaching capacity"
    else:
        data["zones"][zone_id]["alert"] = ""

    log_row(time.strftime("%H:%M:%S"),
            {z: d["count"] for z, d in data["zones"].items()})
