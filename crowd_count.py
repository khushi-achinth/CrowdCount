import os
import cv2
import numpy as np
from collections import defaultdict
from ultralytics import YOLO

# ---------------- CONFIG ----------------
YOLO_MODEL = "yolov8n.pt"
VIDEO_PATH = "video.mp4"     # change if needed
CONF_THRESH = 0.6

IMG_RESIZE = (640, 360)
ZONES_FILE = "zones.npy"

MAX_DISAPPEARED = 30
MAX_DISTANCE = 80
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


# ---------------- CENTROID TRACKER ----------------
class CentroidTracker:
    def __init__(self, max_disappeared=MAX_DISAPPEARED, max_distance=MAX_DISTANCE):
        self.next_id = 1
        self.objects = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, detections):
        rects = [tuple(d[:4]) for d in detections]
        centroids = [xyxy_to_centroid(r) for r in rects]

        if not self.objects:
            for i, r in enumerate(rects):
                self.objects[self.next_id] = {"bbox": r, "centroid": centroids[i], "gone": 0}
                self.next_id += 1
        else:
            obj_ids = list(self.objects.keys())
            obj_centroids = [self.objects[o]["centroid"] for o in obj_ids]

            if centroids:
                D = np.linalg.norm(
                    np.array(obj_centroids)[:, None] -
                    np.array(centroids)[None, :], axis=2
                )
                rows = D.min(axis=1).argsort()
                cols = D.argmin(axis=1)[rows]

                used_r, used_c = set(), set()
                for r, c in zip(rows, cols):
                    if r in used_r or c in used_c:
                        continue
                    if D[r, c] > self.max_distance:
                        continue
                    oid = obj_ids[r]
                    self.objects[oid]["bbox"] = rects[c]
                    self.objects[oid]["centroid"] = centroids[c]
                    self.objects[oid]["gone"] = 0
                    used_r.add(r)
                    used_c.add(c)

                for i, oid in enumerate(obj_ids):
                    if i not in used_r:
                        self.objects[oid]["gone"] += 1
                        if self.objects[oid]["gone"] > self.max_disappeared:
                            del self.objects[oid]

                for j, r in enumerate(rects):
                    if j not in used_c:
                        self.objects[self.next_id] = {
                            "bbox": r,
                            "centroid": centroids[j],
                            "gone": 0
                        }
                        self.next_id += 1

        return [{"id": oid, **v} for oid, v in self.objects.items()]


# ---------------- MAIN ----------------
def main():
    model = YOLO(YOLO_MODEL)
    zones = load_zones()

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("Cannot open video")
        return

    clahe = cv2.createCLAHE(2.0, (8, 8))
    tracker = CentroidTracker()

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

        # YOLO detection
        results = model(inf, conf=CONF_THRESH, verbose=False)
        detections = []

        if results and results[0].boxes:
            for b in results[0].boxes:
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                detections.append([
                    int(x1 * sx), int(y1 * sy),
                    int(x2 * sx), int(y2 * sy),
                    float(b.conf[0])
                ])

        tracks = tracker.update(detections)

        for t in tracks:
            tid = t["id"]
            x1, y1, x2, y2 = t["bbox"]
            cx, cy = t["centroid"]

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
                        (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
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
            try:
                editing_zone_id = int(input("Enter Zone ID to edit: "))
                drawing = True
                current_pts = []
            except ValueError:
                print("Invalid ID")

        elif k == ord('d'):
            try:
                zid = int(input("Enter Zone ID to delete: "))
                zones[:] = [z for z in zones if z["id"] != zid]
                print(f"Zone {zid} deleted")
            except ValueError:
                print("Invalid ID")

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
    print("Final counts:", dict(counts))


if __name__ == "__main__":
    main()
