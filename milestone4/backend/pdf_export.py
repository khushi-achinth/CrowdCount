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
from config import get_thresholds, WARNING_OFFSET

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
CSV_FILE = os.path.join(LOG_DIR, "crowd_data.csv")
PDF_FILE = os.path.join(LOG_DIR, "crowd_report.pdf")


def generate_pdf():
    thresholds = get_thresholds()
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Crowd Monitoring Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    if not os.path.exists(CSV_FILE):
        elements.append(Paragraph("No crowd data available.", styles["Normal"]))
        SimpleDocTemplate(PDF_FILE, pagesize=A4).build(elements)
        return PDF_FILE

    table_data = []
    max_values = {}

    with open(CSV_FILE, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        table_data.append(header)

        # Initialize max values for zones only (skip Timestamp & Total)
        for zone in header[1:-1]:
            max_values[zone] = 0

        for row in reader:
            table_data.append(row)
            for i, zone in enumerate(header[1:-1], start=1):
                max_values[zone] = max(max_values[zone], int(row[i]))

    # -------- DATA TABLE --------
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

    # -------- SUMMARY --------
    elements.append(Paragraph("<b>Zone Summary</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    summary = [["Zone", "Max Count", "Threshold", "Status"]]

    for zone, max_count in max_values.items():
        threshold = thresholds.get(zone, 20)

        if max_count >= threshold:
            status = "Overcrowded"
            color = colors.red
        elif max_count >= threshold - WARNING_OFFSET:
            status = "Approaching Capacity"
            color = colors.orange
        else:
            status = "Safe"
            color = colors.green

        summary.append([zone, str(max_count), str(threshold), status])

    summary_table = Table(summary, repeatRows=1)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    for i in range(1, len(summary)):
        status = summary[i][3]
        summary_table.setStyle([
            ("TEXTCOLOR", (3, i), (3, i),
             colors.red if status == "Overcrowded"
             else colors.orange if status == "Approaching Capacity"
             else colors.green)
        ])

    elements.append(summary_table)

    SimpleDocTemplate(PDF_FILE, pagesize=A4).build(elements)
    return PDF_FILE
