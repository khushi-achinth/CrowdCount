import os, json
from flask import Flask, jsonify, request, send_file, render_template
from flask_cors import CORS
from data_store import data, update
from pdf_export import generate_pdf
from auth import generate_token
from users import USERS
from admin_zones import admin_zones

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

app = Flask(__name__)
CORS(app)
app.register_blueprint(admin_zones)

@app.route("/zone_config")
def get_zone_config():
    with open("zone_config.json", "r") as f:
        return jsonify(json.load(f))

@app.route("/login", methods=["POST"])
def login():
    payload = request.get_json(force=True)
    user = USERS.get(payload.get("username"))

    if not user or user["password"] != payload.get("password"):
        return {"error": "Invalid credentials"}, 401

    return {
        "token": generate_token(payload["username"], user["role"]),
        "role": user["role"]
    }

@app.route("/admin/zones_ui")
def admin_zones_ui():
    return render_template("admin_zones.html")

@app.route("/update_zones", methods=["POST"])
def update_zones():
    zones = request.get_json(force=True).get("zones", {})
    for zid, count in zones.items():
        update(zid, count)
    return {"status": "ok"}

@app.route("/dashboard_data")
def dashboard_data():
    return jsonify(data)

@app.route("/export/csv")
def export_csv():
    return send_file(os.path.join(LOG_DIR, "crowd_data.csv"), as_attachment=True)

@app.route("/export/pdf")
def export_pdf():
    return send_file(generate_pdf(), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=False)
