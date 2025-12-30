from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

from users import USERS
from auth import generate_token, token_required
from data_store import update, data
from pdf_export import generate_pdf

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZONES_FILE = os.path.join(BASE_DIR, "detector", "zones.json")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    payload = request.json
    username = payload.get("username")
    password = payload.get("password")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(username, user["role"])
    return jsonify({"token": token, "role": user["role"]})


# ---------------- DETECTOR UPDATE ----------------
@app.route("/update_zones", methods=["POST"])
def update_zones():
    payload = request.json
    for zone, count in payload.items():
        update(zone, count)
    return {"status": "ok"}


# ---------------- DASHBOARD ----------------
@app.route("/dashboard_data")
@token_required()
def dashboard_data():
    return jsonify(data)


# ---------------- EXPORTS ----------------
@app.route("/export/pdf")
@token_required(required_role="admin")
def export_pdf():
    return generate_pdf()


@app.route("/export/csv")
@token_required(required_role="admin")
def export_csv():
    return jsonify({"message": "CSV already generated"})


# ---------------- GET ZONES ----------------
@app.route("/zones", methods=["GET"])
@token_required(required_role="admin")
def get_zones():
    with open(ZONES_FILE, "r") as f:
        return jsonify(json.load(f)["zones"])


# ---------------- ADD ZONE ----------------
@app.route("/zones/add", methods=["POST"])
@token_required(required_role="admin")
def add_zone():
    payload = request.json

    with open(ZONES_FILE, "r") as f:
        data_json = json.load(f)

    zones = data_json["zones"]
    next_id = max(z["id"] for z in zones) + 1 if zones else 1

    zones.append({
        "id": next_id,
        "name": payload["name"],
        "threshold": int(payload["threshold"]),
        "points": payload["points"]
    })

    with open(ZONES_FILE, "w") as f:
        json.dump({"zones": zones}, f, indent=2)

    return jsonify({"message": "Zone added. Restart system to apply."})


# ---------------- UPDATE ZONE ----------------
@app.route("/zones/update", methods=["PUT"])
@token_required(required_role="admin")
def update_zone():
    payload = request.json
    zone_id = payload.get("id")

    with open(ZONES_FILE, "r") as f:
        data_json = json.load(f)

    for z in data_json["zones"]:
        if z["id"] == zone_id:
            z["name"] = payload.get("name", z["name"])
            z["threshold"] = int(payload.get("threshold", z["threshold"]))
            break

    with open(ZONES_FILE, "w") as f:
        json.dump(data_json, f, indent=2)

    return jsonify({"message": "Zone updated. Restart system to apply."})


# ---------------- DELETE ZONE ----------------
@app.route("/zones/delete/<int:zone_id>", methods=["DELETE"])
@token_required(required_role="admin")
def delete_zone(zone_id):
    with open(ZONES_FILE, "r") as f:
        data_json = json.load(f)

    data_json["zones"] = [z for z in data_json["zones"] if z["id"] != zone_id]

    with open(ZONES_FILE, "w") as f:
        json.dump(data_json, f, indent=2)

    return jsonify({"message": "Zone deleted. Restart system to apply."})


if __name__ == "__main__":
    app.run(debug=True)
