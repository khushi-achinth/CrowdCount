# camera_feed.py
import cv2

def get_camera_frame(camera_idx=0):
    """
    Generator that initializes the camera, yields (ret, frame) pairs,
    and releases the camera when the loop ends or an exception occurs.
    """
    cap = cv2.VideoCapture(camera_idx)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {camera_idx}")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield ret, frame
    finally:
        cap.release()
