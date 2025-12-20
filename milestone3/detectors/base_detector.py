from threading import Thread
import time
import requests
import cv2
import os
from ultralytics import YOLO


latest_count = 0


STOP_FILE = "STOP"
MODEL_PATH = "yolov8n.pt"
UPDATE_INTERVAL = 3

HEATMAP_DIR = "heatmaps"
os.makedirs(HEATMAP_DIR, exist_ok=True)

# Auto-clear STOP file
if os.path.exists(STOP_FILE):
    os.remove(STOP_FILE)

model = YOLO(MODEL_PATH)

def sender(zone):
    while True:
        try:
            requests.post(
                "http://127.0.0.1:5000/update_zone",
                json={"zone": zone, "count": latest_count}
            )
        except:
            pass
        time.sleep(3)


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
            time.sleep(3)

    Thread(target=sender, daemon=True).start()
    # ----------------------------------------------------------

    while cap.isOpened():

        if os.path.exists(STOP_FILE):
            break

        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            frame,
            persist=True,
            classes=[0],
            tracker="bytetrack.yaml"
        )

        count = 0
        if results and results[0].boxes.id is not None:
            count = len(results[0].boxes.id)

        # 🔑 ONLY UPDATE VARIABLE (NO HTTP HERE)
        latest_count = count

        cv2.putText(
            frame,
            f"Zone: {zone_name} | Count: {count}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.imshow(zone_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            open(STOP_FILE, "w").close()
            break

        # 🔑 Yield CPU (VERY IMPORTANT)
        time.sleep(0.01)

    cap.release()
    cv2.destroyAllWindows()
