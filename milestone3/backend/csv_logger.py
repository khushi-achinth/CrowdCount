import csv
import os

CSV_FILE = os.path.join("logs", "crowd_data.csv")
HEADER = ["Time", "Entrance", "Retail", "Food Court", "Total"]

os.makedirs("logs", exist_ok=True)


def ensure_header():
    """
    Ensures CSV exists AND has correct header.
    If file exists without header, rewrite it with header.
    """
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
        return

    # File exists → check first row
    with open(CSV_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        first_row = next(reader, None)

    if first_row != HEADER:
        # Rewrite file with header + old data
        with open(CSV_FILE, "r", newline="") as f:
            rows = list(csv.reader(f))

        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)
            for row in rows:
                writer.writerow(row)


def log_row(time_str, entrance, retail, foodcourt):
    ensure_header()  # 🔥 GUARANTEES HEADER

    total = entrance + retail + foodcourt

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            time_str,
            entrance,
            retail,
            foodcourt,
            total
        ])
