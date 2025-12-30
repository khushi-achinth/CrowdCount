import csv
import os
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from config import THRESHOLDS, WARNING_OFFSET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
CSV_FILE = os.path.join(LOG_DIR, "crowd_data.csv")
PDF_FILE = os.path.join(LOG_DIR, "crowd_report.pdf")


def generate_pdf():
    styles = getSampleStyleSheet()
    elements = []

    # -------- TITLE --------
    elements.append(Paragraph("<b>Crowd Monitoring Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    # -------- HANDLE NO DATA --------
    if not os.path.exists(CSV_FILE):
        elements.append(Paragraph("No crowd data available.", styles["Normal"]))
        doc = SimpleDocTemplate(PDF_FILE, pagesize=A4)
        doc.build(elements)
        return PDF_FILE

    # -------- READ CSV --------
    table_data = []
    max_values = {
        "Entrance": 0,
        "Walk Path": 0,
        "Exit": 0
    }

    with open(CSV_FILE, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        table_data.append(header)

        for row in reader:
            table_data.append(row)
            max_values["Entrance"] = max(max_values["Entrance"], int(row[1]))
            max_values["Walk Path"] = max(max_values["Walk Path"], int(row[2]))
            max_values["Exit"] = max(max_values["Exit"], int(row[3]))

    # -------- CROWD DATA TABLE --------
    elements.append(Paragraph("<b>Recorded Crowd Data</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    data_table = Table(table_data, repeatRows=1)
    data_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(data_table)
    elements.append(Spacer(1, 20))

    # -------- SUMMARY TABLE --------
    elements.append(Paragraph("<b>Zone Summary</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    summary_table_data = [
        ["Zone", "Max Count", "Threshold", "Status"]
    ]

    for zone_name, max_count in max_values.items():
        key = zone_name.lower().replace(" ", "")
        threshold = THRESHOLDS[key]

        if max_count >= threshold:
            status = "Overcrowded"
            color = colors.red
        elif max_count >= threshold - WARNING_OFFSET:
            status = "Approaching Capacity"
            color = colors.orange
        else:
            status = "Safe"
            color = colors.green

        summary_table_data.append([
            zone_name,
            str(max_count),
            str(threshold),
            status
        ])

    summary_table = Table(summary_table_data, repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Color status column
    for i in range(1, len(summary_table_data)):
        status = summary_table_data[i][3]
        if status == "Overcrowded":
            summary_table.setStyle([
                ("TEXTCOLOR", (3, i), (3, i), colors.red)
            ])
        elif status == "Approaching Capacity":
            summary_table.setStyle([
                ("TEXTCOLOR", (3, i), (3, i), colors.orange)
            ])
        else:
            summary_table.setStyle([
                ("TEXTCOLOR", (3, i), (3, i), colors.green)
            ])

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # -------- TEXT SUMMARY --------
    elements.append(Paragraph("<b>Observations</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    for zone, max_count in max_values.items():
        key = zone.lower().replace(" ", "")
        threshold = THRESHOLDS[key]

        if max_count >= threshold:
            text = f"{zone} experienced overcrowding (maximum count: {max_count})."
        elif max_count >= threshold - WARNING_OFFSET:
            text = f"{zone} was approaching capacity (maximum count: {max_count})."
        else:
            text = f"{zone} remained under safe limits (maximum count: {max_count})."

        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 6))

    # -------- BUILD PDF --------
    doc = SimpleDocTemplate(PDF_FILE, pagesize=A4)
    doc.build(elements)

    return PDF_FILE
