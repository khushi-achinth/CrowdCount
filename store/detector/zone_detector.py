import cv2
import json
import time
import requests
import numpy as np
from ultralytics import YOLO
from collections import defaultdict

# ---------------- CONFIG ----------------
YOLO_MODEL = "yolov8n.pt"
VIDEO_PATH = "video.mp4"
ZONES_JSON = "zones.json"
BACKEND_URL = "http://127.0.0.1:5000/update_zones"
IMG_RESIZE = (640, 360)
SEND_INTERVAL = 2
# --------------------------------------

ZONE_MAP = {
    1: "entrance",
    2: "walkpath",
    3: "exit"
}

# OpenCV colors (BGR)
YELLOW = (0, 255, 255)
GREEN = (0, 255, 0)

# ---------------- UTILITIES ----------------
def load_zones():
    with open(ZONES_JSON, "r") as f:
        raw = json.load(f)["zones"]

    zones = []
    for z in raw:
        points = list(zip(z["points"][::2], z["points"][1::2]))
        zones.append({
            "name": ZONE_MAP[z["id"]],
            "points": points
        })
    return zones


def centroid(box):
    x1, y1, x2, y2 = box
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


def point_inside(pt, poly):
    return cv2.pointPolygonTest(
        np.array(poly, np.int32),
        (int(pt[0]), int(pt[1])),
        False
    ) >= 0


# ---------------- MAIN ----------------
def main():
    model = YOLO(YOLO_MODEL)
    zones = load_zones()

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("Error: Cannot open video")
        return

    counts = defaultdict(int)
    last_inside = defaultdict(set)
    last_send = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = frame.copy()
        infer = cv2.resize(frame, IMG_RESIZE)

        sx = frame.shape[1] / IMG_RESIZE[0]
        sy = frame.shape[0] / IMG_RESIZE[1]

        # Initialize heatmap
        heatmap = np.zeros(frame.shape[:2], dtype=np.float32)

        # Draw zones (YELLOW)
        for z in zones:
            cv2.polylines(
                display,
                [np.array(z["points"], np.int32)],
                True,
                YELLOW,
                2
            )
            cv2.putText(
                display,
                z["name"].upper(),
                z["points"][0],
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                YELLOW,
                2
            )

        # YOLO + ByteTrack
        results = model.track(
            infer,
            classes=[0],
            tracker="bytetrack.yaml",
            persist=True,
            verbose=False
        )

        if results and results[0].boxes:
            for box in results[0].boxes:
                if box.id is None:
                    continue

                tid = int(box.id[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                x1, x2 = int(x1 * sx), int(x2 * sx)
                y1, y2 = int(y1 * sy), int(y2 * sy)

                cx, cy = centroid((x1, y1, x2, y2))

                # Accumulate heatmap density
                heatmap[y1:y2, x1:x2] += 1

                # Draw person bounding box (GREEN)
                cv2.rectangle(display, (x1, y1), (x2, y2), GREEN, 2)

                # Draw centroid (GREEN)
                cv2.circle(display, (cx, cy), 4, GREEN, -1)

                # Draw person ID (GREEN)
                cv2.putText(
                    display,
                    f"ID {tid}",
                    (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    GREEN,
                    2
                )

                # Zone-based counting
                inside_now = set()
                for z in zones:
                    if point_inside((cx, cy), z["points"]):
                        inside_now.add(z["name"])
                        if z["name"] not in last_inside[tid]:
                            counts[z["name"]] += 1

                last_inside[tid] = inside_now

        # Heatmap processing
        heatmap = cv2.GaussianBlur(heatmap, (0, 0), 25)
        heatmap_norm = cv2.normalize(
            heatmap, None, 0, 255, cv2.NORM_MINMAX
        ).astype(np.uint8)

        heatmap_color = cv2.applyColorMap(
            heatmap_norm, cv2.COLORMAP_JET
        )

        # Overlay heatmap on video
        display = cv2.addWeighted(display, 0.6, heatmap_color, 0.4, 0)

        # Send counts to backend (dashboard only)
        if time.time() - last_send >= SEND_INTERVAL:
            try:
                requests.post(
                    BACKEND_URL,
                    json={
                        "entrance": counts["entrance"],
                        "walkpath": counts["walkpath"],
                        "exit": counts["exit"]
                    }
                )
            except:
                pass
            last_send = time.time()

        cv2.imshow("Crowd Monitor", display)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()