import os
import time
import cv2
from datetime import datetime
from config import FRAME_WIDTH, FRAME_HEIGHT, CAMERA_WARMUP_FRAMES, MIN_BRIGHTNESS


class WebcamController:
    def __init__(self, camera_index: int = 0, save_folder: str = "captures"):
        self.camera_index = camera_index
        self.save_folder = save_folder
        os.makedirs(self.save_folder, exist_ok=True)

        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam.")

        # Warm up camera
        for _ in range(CAMERA_WARMUP_FRAMES):
            self.cap.read()
            time.sleep(0.05)

    def capture_image(self):
        # Discard a few frames to reduce stale / dark frame issue
        valid_frame = None

        for _ in range(10):
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.03)
                continue

            brightness = frame.mean()
            if brightness > MIN_BRIGHTNESS:
                valid_frame = frame
                break

            time.sleep(0.03)

        if valid_frame is None:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        path = os.path.join(self.save_folder, filename)

        success = cv2.imwrite(path, valid_frame)
        if not success:
            return None

        return path

    def release(self):
        if self.cap is not None:
            self.cap.release()