from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import time
import os

def generate_pdf():
    os.makedirs("logs", exist_ok=True)
    name = f"logs/summary_{time.strftime('%d-%m-%Y_%H-%M-%S')}.pdf"

    c = canvas.Canvas(name, pagesize=A4)
    c.drawString(50, 800, "CrowdCount – Daily Summary Report")
    c.drawString(50, 770, f"Generated: {time.strftime('%d-%m-%Y %H:%M:%S')}")
    c.drawString(50, 740, "Zone-wise crowd analytics")

    c.save()
    return name
