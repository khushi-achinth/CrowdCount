import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONES_FILE = os.path.join(BASE_DIR, "zones.json")

DEFAULT_THRESHOLD = 20
WARNING_OFFSET = 3


def load_zones():
    if not os.path.exists(ZONES_FILE):
        return []

    with open(ZONES_FILE, "r") as f:
        return json.load(f).get("zones", [])


def get_thresholds():
    """
    Returns:
    {
      "Entrance": 20,
      "Walk Path": 20,
      "Exit": 20,
      ...
    }
    """
    zones = load_zones()
    return {
        z["name"]: z.get("threshold", DEFAULT_THRESHOLD)
        for z in zones
    }


# 🔒 BACKWARD-COMPATIBILITY LAYER (DO NOT REMOVE)
# This ensures Milestone 3 code (PDF / alerts) continues to work
THRESHOLDS = get_thresholds()
