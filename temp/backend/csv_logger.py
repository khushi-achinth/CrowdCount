import csv
import os

CSV_FILE = "crowd_log.csv"

def log_row(timestamp, zone_counts: dict):
    """
    zone_counts example:
    { "1": 5, "4": 2 }
    """

    file_exists = os.path.exists(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)

        # Write header once
        if not file_exists:
            header = ["time"] + [f"zone_{z}" for z in zone_counts.keys()]
            writer.writerow(header)

        row = [timestamp] + list(zone_counts.values())
        writer.writerow(row)
