import os
import sys
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from backend.data_store import data, update
from backend.pdf_export import generate_pdf

app = Flask(__name__)
CORS(app)

# ---------- RECEIVE UPDATES ----------
@app.route("/update_zone", methods=["POST"])
def update_zone():
    payload = request.get_json(force=True)
    update(payload["zone"], payload["count"])
    return {"status": "ok"}

# ---------- DASHBOARD DATA ----------
@app.route("/dashboard_data")
def dashboard_data():
    safe = {"zones": {}, "time": list(data["time"])}

    for z, info in data["zones"].items():
        safe["zones"][z] = {
            "count": int(info["count"]),
            "history": list(info["history"]),
            "alert": bool(info["alert"])
        }

    return jsonify(safe)

# ---------- CSV DOWNLOAD ----------
@app.route("/export/csv")
def export_csv():
    csv_path = os.path.join(os.getcwd(), "logs", "crowd_data.csv")
    return send_file(csv_path, as_attachment=True)

# ---------- PDF DOWNLOAD ----------
@app.route("/export/pdf")
def export_pdf():
    pdf_path = generate_pdf()
    return send_file(os.path.abspath(pdf_path), as_attachment=True)

# ---------- HEATMAP IMAGE ----------
@app.route("/heatmap/<zone>")
def heatmap(zone):
    path = os.path.join(os.getcwd(), "heatmaps", f"{zone}.jpg")
    if not os.path.exists(path):
        return "", 404
    return send_file(path, mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(port=5000, debug=False)
