import cv2
import time
import os
import requests
import numpy as np
from threading import Thread
from ultralytics import YOLO

# ---------------- CONFIG ----------------
STOP_FILE = "STOP"
MODEL_PATH = "yolov8n.pt"
UPDATE_INTERVAL = 3  # seconds
# --------------------------------------

# Remove STOP file on fresh start
if os.path.exists(STOP_FILE):
    os.remove(STOP_FILE)

model = YOLO(MODEL_PATH)

# Shared variable for sender thread
latest_count = 0


def run(video_path, zone_name):
    global latest_count

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        return

    cv2.namedWindow(zone_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(zone_name, 640, 360)

    # ---------------- BACKGROUND SENDER THREAD ----------------
    def sender():
        while True:
            if os.path.exists(STOP_FILE):
                break
            try:
                requests.post(
                    "http://127.0.0.1:5000/update_zone",
                    json={"zone": zone_name, "count": latest_count}
                )
            except:
                pass
            time.sleep(UPDATE_INTERVAL)

    Thread(target=sender, daemon=True).start()
    # ----------------------------------------------------------

    while cap.isOpened():

        if os.path.exists(STOP_FILE):
            break

        ret, frame = cap.read()
        if not ret:
            break

        # ---------------- YOLO + BYTE TRACK ----------------
        results = model.track(
            frame,
            persist=True,
            classes=[0],
            tracker="bytetrack.yaml"
        )

        count = 0
        density_map = np.zeros(frame.shape[:2], dtype=np.float32)

        if results and results[0].boxes.xyxy is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id
            if ids is not None:
                ids = ids.cpu().numpy()

            count = len(boxes)

            for i, (x1, y1, x2, y2) in enumerate(boxes.astype(int)):
                person_id = int(ids[i]) if ids is not None else -1

                # -------- Bounding Box --------
                cv2.rectangle(
                    frame, (x1, y1), (x2, y2), (0, 255, 0), 2
                )

                # -------- ID Label --------
                cv2.putText(
                    frame,
                    f"ID {person_id}",
                    (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                # -------- Centroid Calculation --------
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                # -------- Draw Centroid --------
                cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
                cv2.putText(
                    frame,
                    f"({cx},{cy})",
                    (cx + 5, cy - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 0, 255),
                    1
                )

                # -------- Density Accumulation --------
                density_map[y1:y2, x1:x2] += 200

        # ---------------- HEATMAP PROCESSING ----------------
        density_map = cv2.GaussianBlur(density_map, (0, 0), 25)

        density_norm = cv2.normalize(
            density_map, None, 0, 255, cv2.NORM_MINMAX
        ).astype(np.uint8)

        heatmap_color = cv2.applyColorMap(
            density_norm, cv2.COLORMAP_JET
        )

        overlay = cv2.addWeighted(
            frame, 0.6, heatmap_color, 0.4, 0
        )

        # ---------------- UPDATE SHARED COUNT ----------------
        latest_count = count

        cv2.putText(
            overlay,
            f"Zone: {zone_name} | Count: {count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.imshow(zone_name, overlay)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            open(STOP_FILE, "w").close()
            break

        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()
