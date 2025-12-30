import json
import os
from flask import Blueprint, request, jsonify
from auth import require_admin

admin_zones = Blueprint("admin_zones", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONES_FILE = os.path.join(BASE_DIR, "detector", "zones.json")


def load_zones():
    if not os.path.exists(ZONES_FILE):
        return {"zones": []}
    with open(ZONES_FILE, "r") as f:
        return json.load(f)


def save_zones(data):
    with open(ZONES_FILE, "w") as f:
        json.dump(data, f, indent=2)


@admin_zones.route("/admin/zones", methods=["GET"])
@require_admin
def get_zones():
    return jsonify(load_zones())


@admin_zones.route("/admin/zones", methods=["POST"])
@require_admin
def add_zone():
    payload = request.get_json(force=True)

    zone_id = payload["id"]
    points = payload["points"]
    name = payload.get("name", f"Zone {zone_id}")
    threshold = payload.get("threshold", 10)

    # ---- update zones.json (geometry only) ----
    zones_data = load_zones()
    zones_data["zones"] = [z for z in zones_data["zones"] if z["id"] != zone_id]
    zones_data["zones"].append({
        "id": zone_id,
        "points": points
    })
    save_zones(zones_data)

    # ---- update zone_config.json (metadata) ----
    config_file = os.path.join(BASE_DIR, "backend", "zone_config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)
    else:
        config = {}

    config[str(zone_id)] = {
        "name": name,
        "threshold": threshold
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    return {"status": "zone saved"}



@admin_zones.route("/admin/zones/<int:zone_id>", methods=["DELETE"])
@require_admin
def delete_zone(zone_id):
    data = load_zones()
    data["zones"] = [z for z in data["zones"] if z["id"] != zone_id]
    save_zones(data)
    return {"status": "zone deleted"}
