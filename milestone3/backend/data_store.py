from collections import deque
from backend.csv_logger import log
from backend.config import THRESHOLDS
import time

data = {
    "zones": {
        "entrance": {"count": 0, "history": deque(maxlen=60), "alert": False},
        "retail": {"count": 0, "history": deque(maxlen=60), "alert": False},
        "foodcourt": {"count": 0, "history": deque(maxlen=60), "alert": False},
    },
    "time": deque(maxlen=60)
}

def update(zone, count):
    z = data["zones"][zone]
    z["count"] = count
    z["history"].append(count)
    z["alert"] = count > THRESHOLDS[zone]
    log(zone, count)

    if zone == "entrance":
        data["time"].append(time.strftime("%H:%M:%S"))
