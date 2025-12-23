import os
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from data_store import data, update
from pdf_export import generate_pdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")

app = Flask(__name__)
CORS(app)

@app.route("/update_zones", methods=["POST"])
def update_zones():
    payload = request.get_json(force=True)
    for zone, count in payload.items():
        update(zone, count)
    return {"status": "ok"}

@app.route("/dashboard_data")
def dashboard_data():
    return jsonify(data)

@app.route("/export/csv")
def export_csv():
    csv_path = os.path.join(LOG_DIR, "crowd_data.csv")
    if not os.path.exists(csv_path):
        return {"error": "CSV not found"}, 404
    return send_file(csv_path, as_attachment=True)

@app.route("/export/pdf")
def export_pdf():
    pdf_path = generate_pdf()
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
