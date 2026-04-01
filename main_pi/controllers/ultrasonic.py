# controllers/ultrasonic.py
from gpiozero import DistanceSensor
from gpiozero.exc import DistanceSensorNoEcho


class UltrasonicController:
    def __init__(self, trigger_pin: int, echo_pin: int):
        self.sensor = DistanceSensor(
            echo=echo_pin,
            trigger=trigger_pin,
            max_distance=2.0,
            threshold_distance=0.3,
        )

    def get_distance_cm(self):
        try:
            return self.sensor.distance * 100.0
        except DistanceSensorNoEcho:
            return None
        except Exception as e:
            print(f"[ULTRASONIC ERROR] {e}")
            return None

    def cleanup(self):
        try:
            self.sensor.close()
        except Exception:
            pass