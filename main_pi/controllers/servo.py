import os
import time
from gpiozero import Servo
from gpiozero.pins.lgpio import LGPIOFactory

# Force gpiozero to use lgpio backend on Raspberry Pi 5
os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"


class ServoController:
    def __init__(self, gpio_pin: int, name: str = "SERVO"):
        self.name = name
        self.gpio_pin = gpio_pin
        self.factory = LGPIOFactory()

        self.servo = Servo(
            pin=gpio_pin,
            pin_factory=self.factory,
            min_pulse_width=0.0005,
            max_pulse_width=0.0025,
        )

    @staticmethod
    def angle_to_value(angle: float) -> float:
        # Maps 0..180 degrees to gpiozero servo range -1..1
        angle = max(0, min(180, angle))
        return (angle / 90.0) - 1.0

    def move_to(self, angle: float, settle_s: float = 0.8):
        try:
            value = self.angle_to_value(angle)
            print(f"[{self.name}] Moving to {angle}° (value={value:.2f})")
            self.servo.value = value
            time.sleep(settle_s)
            self.servo.detach()  # reduce jitter after movement
        except Exception as e:
            print(f"[{self.name} ERROR] {e}")

    def cleanup(self):
        try:
            self.servo.detach()
            self.servo.close()
        except Exception:
            pass