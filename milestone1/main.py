# main.py
import cv2
from milestone1.camera_feed import get_camera_frame
from milestone1.zones import load_zones, save_zones, ZoneManager

def main():
    window_name = "Webcam"
    cv2.namedWindow(window_name)

    # Load zones and create manager
    rois = load_zones("zones.json")
    zm = ZoneManager(rois)

    # Set mouse callback (pass ZoneManager instance as param)
    cv2.setMouseCallback(window_name, ZoneManager.mouse_callback, zm)

    print("""
    Controls:
    - Draw zones with mouse → new numeric ID assigned automatically
    - Press 's' to save all to zones.json
    - Press 'q' to quit
    - Press 'e' to edit a zone (enter zone ID and redraw it)
    - Press 'd' to delete a zone (enter zone ID to delete)
    - Press 'n' to return to drawing mode
    """)

    try:
        for ret, frame in get_camera_frame(0):
            if not ret:
                break

            # Draw zones
            zm.draw_zones(frame)

            # Draw current drag rectangle if drawing
            drag = zm.get_current_drag_rect()
            if drag:
                x1, y1, x2, y2 = drag
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Mode text
            mode_text = f"Mode: {zm.mode.upper()}"
            if zm.selected_zone is not None:
                mode_text += f" | Editing ID: {zm.selected_zone}"
            if zm.editing_zone:
                mode_text += " | DRAW NEW AREA"
            cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('s'):
                save_zones(zm.rois, "zones.json")
            elif key == ord('e'):
                zm.mode = "edit"
                zone_id_str = input("Enter zone ID to edit: ")
                try:
                    zone_id = int(zone_id_str)
                    zm.start_edit(zone_id)
                except ValueError:
                    print("Invalid ID (must be integer).")
                    zm.set_mode_draw()
            elif key == ord('d'):
                zm.mode = "delete"
                zone_id_str = input("Enter zone ID to delete: ")
                try:
                    zone_id = int(zone_id_str)
                    zm.delete_zone(zone_id)
                except ValueError:
                    print("Invalid ID (must be integer).")
                zm.set_mode_draw()
            elif key == ord('n'):
                zm.set_mode_draw()
                print("Drawing mode: Draw new zones with mouse")
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
