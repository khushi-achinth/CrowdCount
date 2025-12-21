import os
import sys
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

from backend.data_store import data, update
from backend.pdf_export import generate_pdf

app = Flask(__name__)
CORS(app)

@app.route("/update_zone", methods=["POST"])
def update_zone():
    payload = request.get_json(force=True)
    update(payload["zone"], payload["count"])
    return {"status": "ok"}

@app.route("/dashboard_data")
def dashboard_data():
    return jsonify(data)

@app.route("/export/csv")
def export_csv():
    return send_file(os.path.join(os.getcwd(), "logs", "crowd_data.csv"), as_attachment=True)

@app.route("/export/pdf")
def export_pdf():
    pdf_path = generate_pdf()
    return send_file(os.path.abspath(pdf_path), as_attachment=True)

if __name__ == "__main__":
    app.run(port=5000, debug=False)
