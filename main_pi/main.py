import os
import time
from controllers.ultrasonic import UltrasonicController
from controllers.webcam import WebcamController
from controllers.servo import ServoController
from ai.classifier import WasteClassifier

from config import (
    TRIG,
    ECHO,
    TRIGGER_DISTANCE_CM,
    CAPTURE_COOLDOWN_S,
    CHECK_DELAY_S,
    CAMERA_INDEX,
    SAVE_FOLDER,
    BIN_SERVO_GPIO,
    RELEASE_SERVO_GPIO,
    NEUTRAL_ANGLE,
    RELEASE_OPEN_ANGLE,
    RELEASE_CLOSE_ANGLE,
    BIN_ANGLES,
    CLEAR_DISTANCE_CM,
    PRESENT_COUNT,
    CLEAR_COUNT,
    SERVO_SETTLE_S,
    RELEASE_HOLD_S,
)


def ensure_folder(path: str):
    os.makedirs(path, exist_ok=True)


# Move rotating chute / selector to correct bin
# Returns True if a known label was routed successfully
# Returns False if label is unknown and system falls back to neutral

def route_to_bin(bin_servo: ServoController, label: str) -> bool:
    angle = BIN_ANGLES.get(label)
    if angle is None:
        print(f"[ROUTE] Unknown label '{label}', going to NEUTRAL.")
        bin_servo.move_to(NEUTRAL_ANGLE, settle_s=SERVO_SETTLE_S)
        return False

    print(f"[ROUTE] {label} -> bin angle {angle}°")
    bin_servo.move_to(angle, settle_s=SERVO_SETTLE_S)
    return True


# Open and close the release platform/trapdoor

def release_item(release_servo: ServoController):
    print(f"[RELEASE] Opening platform at {RELEASE_OPEN_ANGLE}°")
    release_servo.move_to(RELEASE_OPEN_ANGLE, settle_s=SERVO_SETTLE_S)
    time.sleep(RELEASE_HOLD_S)

    print(f"[RELEASE] Closing platform at {RELEASE_CLOSE_ANGLE}°")
    release_servo.move_to(RELEASE_CLOSE_ANGLE, settle_s=SERVO_SETTLE_S)
    time.sleep(0.4)


# Optional: return rotating bin selector to neutral after each item

def reset_bin_position(bin_servo: ServoController):
    print(f"[RESET] Returning bin selector to NEUTRAL ({NEUTRAL_ANGLE}°)")
    bin_servo.move_to(NEUTRAL_ANGLE, settle_s=SERVO_SETTLE_S)


def main():
    print("[SYSTEM] Starting Edge Smart Recycling Bin...")
    ensure_folder(SAVE_FOLDER)

    ultrasonic = UltrasonicController(
        trigger_pin=TRIG,
        echo_pin=ECHO,
    )
    camera = WebcamController(
        camera_index=CAMERA_INDEX,
        save_folder=SAVE_FOLDER,
    )
    bin_servo = ServoController(BIN_SERVO_GPIO, name="BIN")
    release_servo = ServoController(RELEASE_SERVO_GPIO, name="RELEASE")
    classifier = WasteClassifier()

    # Initial positions
    bin_servo.move_to(NEUTRAL_ANGLE, settle_s=SERVO_SETTLE_S)
    release_servo.move_to(RELEASE_CLOSE_ANGLE, settle_s=SERVO_SETTLE_S)

    last_capture_time = 0.0
    present_counter = 0
    clear_counter = 0
    object_confirmed_present = False

    print("[SYSTEM] Ready. Waiting for waste item...")

    try:
        while True:
            distance_cm = ultrasonic.get_distance_cm()

            if distance_cm is None:
                print("[ULTRASONIC] No echo received.")
                time.sleep(CHECK_DELAY_S)
                continue

            print(f"[ULTRASONIC] Distance: {distance_cm:.2f} cm")

            # Object present if it is within trigger distance
            if distance_cm <= TRIGGER_DISTANCE_CM:
                present_counter += 1
                clear_counter = 0
            elif distance_cm >= CLEAR_DISTANCE_CM:
                clear_counter += 1
                present_counter = 0
            else:
                # In-between zone; don't aggressively switch state
                pass

            # Confirm object presence
            if not object_confirmed_present and present_counter >= PRESENT_COUNT:
                object_confirmed_present = True
                now = time.time()

                if now - last_capture_time >= CAPTURE_COOLDOWN_S:
                    print("[SYSTEM] Object confirmed present. Capturing image...")
                    last_capture_time = now

                    image_path = camera.capture_image()
                    if image_path is None:
                        print("[CAMERA] Failed to capture image.")
                        time.sleep(CHECK_DELAY_S)
                        continue

                    print(f"[CAMERA] Image saved: {image_path}")

                    # Classification
                    label, confidence, latency_ms = classifier.classify_image(image_path)
                    print(
                        f"[AI] Prediction: {label} | Confidence: {confidence:.3f} | "
                        f"Inference: {latency_ms:.2f} ms"
                    )

                    # Route and release
                    route_to_bin(bin_servo, label)
                    release_item(release_servo)
                    reset_bin_position(bin_servo)
                else:
                    print("[SYSTEM] Cooldown active, skipping capture.")

            # Confirm object removed
            if object_confirmed_present and clear_counter >= CLEAR_COUNT:
                object_confirmed_present = False
                present_counter = 0
                clear_counter = 0
                print("[SYSTEM] Platform clear. Ready for next item.")

            time.sleep(CHECK_DELAY_S)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Stopping project...")
    finally:
        camera.release()
        bin_servo.cleanup()
        release_servo.cleanup()
        ultrasonic.cleanup()
        print("[SYSTEM] Shutdown complete.")


if __name__ == "__main__":
    main()