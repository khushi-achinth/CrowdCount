# zones.py
import json
import cv2

def rect_sorted(x1, y1, x2, y2):
    """
    Return (x1,y1,x2,y2) with sorted coordinates (top-left, bottom-right).
    """
    xs = sorted([int(x1), int(x2)])
    ys = sorted([int(y1), int(y2)])
    return xs[0], ys[0], xs[1], ys[1]

def load_zones(path="zones.json"):
    """
    Loads zones.json with structure:
    { "zones": [ {"id": 1, "points":[x1,y1,x2,y2]}, ... ] }
    Returns dict {id: [points]}
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)
        rois = {}
        for item in data.get("zones", []):
            zone_id = int(item["id"])
            rois[zone_id] = list(map(int, item["points"]))
        print(f"Loaded {len(rois)} zones from {path}")
        return rois
    except Exception:
        print("No existing zones in the file")
        return {}

def save_zones(rois, path="zones.json"):
    """
    Saves rois dict {id: [points]} into the required JSON format.
    """
    data = {"zones": []}
    for zone_id, points in rois.items():
        data["zones"].append({"id": int(zone_id), "points": list(map(int, points))})
    with open(path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved {len(rois)} zones to {path}")

class ZoneManager:
    def __init__(self, rois=None):
        """
        rois: dict mapping int id -> [x1,y1,x2,y2]
        """
        self.rois = rois if rois else {}
        # Drawing/edit state
        self.drawing = False
        self.start_x = self.start_y = -1
        self.current_x = self.current_y = -1
        self.selected_zone = None   # integer id or None
        self.mode = "draw"          # "draw", "edit", "delete"
        self.editing_zone = False

    @staticmethod
    def mouse_callback(event, x, y, flags, param):
        """
        OpenCV mouse callback. param should be ZoneManager instance.

        Behavior change: when creating a NEW zone (not editing), the user is
        prompted to type the integer ID they want to assign to the zone.
        If the ID already exists, user is asked whether to overwrite.
        Invalid inputs cancel creation.
        """
        zm = param
        if zm.mode == "draw" or (zm.mode == "edit" and zm.editing_zone):
            if event == cv2.EVENT_LBUTTONDOWN:
                zm.drawing = True
                zm.start_x, zm.start_y = x, y
                zm.current_x, zm.current_y = x, y
            elif event == cv2.EVENT_MOUSEMOVE:
                if zm.drawing:
                    zm.current_x, zm.current_y = x, y
            elif event == cv2.EVENT_LBUTTONUP:
                zm.drawing = False
                zm.current_x, zm.current_y = x, y
                x1, y1, x2, y2 = rect_sorted(zm.start_x, zm.start_y, zm.current_x, zm.current_y)

                if zm.selected_zone is not None and zm.editing_zone:
                    # update existing zone (selected_zone is integer id)
                    zm.rois[zm.selected_zone] = [x1, y1, x2, y2]
                    print(f"Updated zone ID: {zm.selected_zone}")
                    zm.selected_zone = None
                    zm.editing_zone = False
                    zm.mode = "draw"
                else:
                    # NEW zone creation: ask user for the desired ID (int)
                    try:
                        id_str = input("Enter integer ID for this zone (leave blank to cancel): ").strip()
                    except EOFError:
                        # in some environments input may raise EOFError; cancel in that case
                        print("No input available — cancelling zone creation.")
                        return

                    if id_str == "":
                        print("Zone creation cancelled.")
                        return

                    # validate integer
                    try:
                        zone_id = int(id_str)
                    except ValueError:
                        print("Invalid ID (must be integer). Zone creation cancelled.")
                        return

                    # if exists, ask whether to overwrite
                    if zone_id in zm.rois:
                        try:
                            resp = input(f"Zone ID {zone_id} already exists. Overwrite? (y/n): ").strip().lower()
                        except EOFError:
                            print("No input available — cancelling zone creation.")
                            return
                        if resp not in ("y", "yes"):
                            print("Zone creation cancelled (did not overwrite).")
                            return

                    # save the zone with the user-provided id
                    zm.rois[zone_id] = [x1, y1, x2, y2]
                    print(f"Added/Updated zone ID: {zone_id}")

    def draw_zones(self, frame):
        """
        Draw all zones onto frame. Labels show the numeric ID.
        """
        for zone_id, coords in self.rois.items():
            if not (isinstance(coords, (list, tuple)) and len(coords) == 4):
                continue
            x1, y1, x2, y2 = map(int, coords)
            color = (0, 0, 255)
            thickness = 2
            if zone_id == self.selected_zone:
                color = (255, 255, 0)
                thickness = 3
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            label = str(zone_id)
            cv2.putText(frame, label, (x1, max(y1 - 5, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    def start_edit(self, zone_id):
        """
        Begin editing an existing zone by ID (int). Returns True if successful.
        """
        if zone_id in self.rois:
            self.selected_zone = zone_id
            self.editing_zone = True
            self.mode = "edit"
            print(f"Selected zone ID {zone_id} for editing. Now draw the new area for this zone.")
            return True
        else:
            print(f"Zone ID '{zone_id}' not found")
            self.mode = "draw"
            return False

    def delete_zone(self, zone_id):
        """
        Delete the zone from memory (not saved until save_zones called).
        """
        if zone_id in self.rois:
            del self.rois[zone_id]
            print(f"Deleted zone ID {zone_id}. Press 's' to save changes.")
            return True
        else:
            print(f"Zone ID '{zone_id}' not found")
            return False

    def preview_zone(self, zone_id):
        return self.rois.get(zone_id)

    def set_mode_draw(self):
        self.mode = "draw"
        self.selected_zone = None
        self.editing_zone = False

    def get_current_drag_rect(self):
        if self.drawing:
            return rect_sorted(self.start_x, self.start_y, self.current_x, self.current_y)
        return None
