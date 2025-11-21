import cv2
import json

drawing = False
start_x, start_y = -1, -1
current_x, current_y = -1, -1
rois = {}
selected_zone = None
mode = "draw"  # Modes: "draw", "edit", "delete"
editing_zone = False  # Flag to track if we're in the process of editing a zone

def mouse(event, x, y, flags, param):
    global drawing, start_x, start_y, current_x, current_y, selected_zone, editing_zone, mode
    
    if mode == "draw" or (mode == "edit" and editing_zone):
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            start_x, start_y = x, y
            current_x, current_y = x, y
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                current_x, current_y = x, y
                
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            current_x, current_y = x, y
            x1, x2 = sorted([start_x, current_x])
            y1, y2 = sorted([start_y, current_y])
            
            # If we're editing an existing zone, use the selected name
            if selected_zone and editing_zone:
                rois[selected_zone] = [x1, y1, x2, y2]
                print(f"Updated zone: {selected_zone}")
                selected_zone = None
                editing_zone = False
                mode = "draw"  # Return to draw mode after editing
            else:
                # Otherwise, ask for a new name
                name = input("Zone name: ")
                if name:
                    rois[name] = [x1, y1, x2, y2]
                    print(f"Added {name} to memory")

# Load existing zones 
try:
    with open('zones.json', 'r') as f:
        rois = json.load(f)
    print(f"Loaded {len(rois)} zones")
except:
    print("No existing zones in the file")

cap = cv2.VideoCapture(0)
cv2.namedWindow("webcam")
cv2.setMouseCallback("webcam", mouse)

print("""
Controls:
- Draw zones → Name them → Press 's' to save all → Press 'q' to quit
- Press 'e' to edit a zone (enter zone name and redraw it)
- Press 'd' to delete a zone (enter zone name to delete)
- Press 'n' to return to normal drawing mode
- All changes (add/edit/delete) are saved ONLY when pressing 's'
""")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Draw saved zones
    for name, (x1, y1, x2, y2) in rois.items():
        color = (0, 0, 255)  # Red for normal zones
        thickness = 2
        
        if name == selected_zone:
            color = (255, 255, 0)  # Cyan for zone being edited
            thickness = 3
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(frame, name, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # Draw current zone while dragging
    if drawing:
        cv2.rectangle(frame, (start_x, start_y), (current_x, current_y), (0, 255, 0), 2)
    
    # Display current mode
    mode_text = f"Mode: {mode.upper()}"
    if selected_zone:
        mode_text += f" | Editing: {selected_zone}"
    if editing_zone:
        mode_text += " | DRAW NEW AREA"
    cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow("webcam", frame)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        with open('zones.json', 'w') as f:
            json.dump(rois, f, indent=4)
        print(f"Saved {len(rois)} zones to file")
    elif key == ord('e'):
        mode = "edit"
        zone_name = input("Enter zone name to edit: ")
        if zone_name in rois:
            selected_zone = zone_name
            editing_zone = True
            print(f"Selected '{zone_name}' for editing. Now draw the new area for this zone.")
        else:
            print(f"Zone '{zone_name}' not found")
            mode = "draw"
    elif key == ord('d'):
        mode = "delete"
        zone_name = input("Enter zone name to delete: ")
        if zone_name in rois:
            del rois[zone_name]
            print(f"Marked zone '{zone_name}' for deletion. Press 's' to save changes.")
        else:
            print(f"Zone '{zone_name}' not found")
        mode = "draw"  # Return to draw mode after deletion
    elif key == ord('n'):
        mode = "draw"
        selected_zone = None
        editing_zone = False
        print("Drawing mode: Draw new zones with mouse")

cap.release()
cv2.destroyAllWindows()