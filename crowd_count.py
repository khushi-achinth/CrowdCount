import os
import cv2
import numpy as np
from collections import defaultdict
from ultralytics import YOLO

# ---------------- CONFIG ----------------
YOLO_MODEL = "yolov8n.pt"
VIDEO_PATH = "video.mp4"
CONF_THRESH = 0.6
IMG_RESIZE = (640, 360)
ZONES_FILE = "zones.npy"
# --------------------------------------


# ---------------- UTILITIES ----------------
def xyxy_to_centroid(b):
    x1, y1, x2, y2 = b
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


def point_in_poly(pt, poly):
    return cv2.pointPolygonTest(
        np.array(poly, np.int32),
        (int(pt[0]), int(pt[1])),
        False
    ) >= 0


def load_zones():
    if os.path.exists(ZONES_FILE):
        return list(np.load(ZONES_FILE, allow_pickle=True))
    return []


def save_zones(zones):
    np.save(ZONES_FILE, np.array(zones, dtype=object))
    print("Zones saved")


# ---------------- MAIN ----------------
def main():
    model = YOLO(YOLO_MODEL)
    zones = load_zones()

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("Cannot open video")
        return

    clahe = cv2.createCLAHE(2.0, (8, 8))

    counts = defaultdict(int)
    counted = set()
    last_inside = defaultdict(set)

    drawing = False
    current_pts = []
    editing_zone_id = None

    def mouse(event, x, y, flags, param):
        nonlocal drawing, current_pts
        if drawing and event == cv2.EVENT_LBUTTONDOWN:
            current_pts.append((x, y))

    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Frame", 960, 540)
    cv2.setMouseCallback("Frame", mouse)

    print("""
Controls:
z - draw zone
n - finish drawing
e - edit zone
d - delete zone
s - save zones
q - quit
""")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ---- CCTV GRAYSCALE FIX ----
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = clahe.apply(gray)
        frame = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        display = frame.copy()
        inf = cv2.resize(frame, IMG_RESIZE)

        sx = frame.shape[1] / IMG_RESIZE[0]
        sy = frame.shape[0] / IMG_RESIZE[1]

        # Draw zones
        for z in zones:
            cv2.polylines(display, [np.array(z["points"], np.int32)], True, (0, 255, 0), 2)
            cv2.putText(display, f"Zone {z['id']}", z["points"][0],
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if drawing and len(current_pts) > 1:
            cv2.polylines(display, [np.array(current_pts, np.int32)], False, (0, 255, 255), 2)

        # ✅ YOLOv8 + ByteTrack
        results = model.track(
            inf,
            conf=CONF_THRESH,
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

                cx, cy = xyxy_to_centroid((x1, y1, x2, y2))

                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.circle(display, (cx, cy), 4, (255, 0, 0), -1)

                inside_now = set()
                for z in zones:
                    zid = z["id"]
                    if point_in_poly((cx, cy), z["points"]):
                        inside_now.add(zid)
                        if zid not in last_inside[tid] and (tid, zid) not in counted:
                            counts[zid] += 1
                            counted.add((tid, zid))
                            print(f"Counted person {tid} in Zone {zid}")

                last_inside[tid] = inside_now

                cv2.putText(display, f"ID {tid}", (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        y = 30
        for z in zones:
            cv2.putText(display, f"Zone {z['id']} Count: {counts[z['id']]}",
                        (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y += 30

        cv2.imshow("Frame", display)

        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            break
        elif k == ord('z'):
            drawing = True
            editing_zone_id = None
            current_pts = []
        elif k == ord('e'):
            editing_zone_id = int(input("Enter Zone ID to edit: "))
            drawing = True
            current_pts = []
        elif k == ord('d'):
            zid = int(input("Enter Zone ID to delete: "))
            zones[:] = [z for z in zones if z["id"] != zid]
        elif k == ord('n'):
            drawing = False
            if len(current_pts) >= 3:
                if editing_zone_id is not None:
                    zones[:] = [z for z in zones if z["id"] != editing_zone_id]
                    zones.append({"id": editing_zone_id, "points": current_pts.copy()})
                    print(f"Zone {editing_zone_id} updated")
                else:
                    zid = int(input("Zone ID: "))
                    zones.append({"id": zid, "points": current_pts.copy()})
                    print(f"Zone {zid} added")
            current_pts = []
            editing_zone_id = None
        elif k == ord('s'):
            save_zones(zones)

    cap.release()
    cv2.destroyAllWindows()
    print("Final counts:")
    for zid in sorted(counts.keys()):
        print(f"Zone {zid}: {counts[zid]}")



if __name__ == "__main__":
    main()
