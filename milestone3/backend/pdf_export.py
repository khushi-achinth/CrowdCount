import csv
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

CSV_FILE = os.path.join("logs", "crowd_data.csv")
PDF_FILE = os.path.join("logs", "crowd_report.pdf")

THRESHOLD = 30
WARNING_OFFSET = 5


def generate_pdf():
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Crowd Monitoring Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    if not os.path.exists(CSV_FILE):
        elements.append(Paragraph("No data available.", styles["Normal"]))
        doc = SimpleDocTemplate(PDF_FILE, pagesize=A4)
        doc.build(elements)
        return PDF_FILE

    table_data = []
    max_values = {"Entrance": 0, "Retail": 0, "Food Court": 0}

    with open(CSV_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            table_data.append(row)
            if i > 0 and len(row) >= 4:
                max_values["Entrance"] = max(max_values["Entrance"], int(row[1]))
                max_values["Retail"] = max(max_values["Retail"], int(row[2]))
                max_values["Food Court"] = max(max_values["Food Court"], int(row[3]))

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ]))

    elements.append(Paragraph("<b>Recorded Crowd Data</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))
    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<b>Summary</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    for zone, value in max_values.items():
        if value >= THRESHOLD:
            text = f"{zone} was overcrowded (max count: {value})."
        elif value >= THRESHOLD - WARNING_OFFSET:
            text = f"{zone} was approaching capacity (max count: {value})."
        else:
            text = f"{zone} remained under safe limits (max count: {value})."

        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 6))

    doc = SimpleDocTemplate(PDF_FILE, pagesize=A4)
    doc.build(elements)

    return PDF_FILE
