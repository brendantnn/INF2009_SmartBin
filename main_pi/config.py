# =========================
# Ultrasonic Sensor
# =========================
TRIG = 23
ECHO = 24
TRIGGER_DISTANCE_CM = 30.0
CAPTURE_COOLDOWN_S = 3.0
CHECK_DELAY_S = 0.2

# Stability settings
CLEAR_DISTANCE_CM = 20.0
PRESENT_COUNT = 3
CLEAR_COUNT = 3

# =========================
# Camera
# =========================
CAMERA_INDEX = 0
SAVE_FOLDER = "captures"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_WARMUP_FRAMES = 8
MIN_BRIGHTNESS = 5

# =========================
# Servo
# =========================
BIN_SERVO_GPIO = 12
RELEASE_SERVO_GPIO = 18
NEUTRAL_ANGLE = 90
RELEASE_OPEN_ANGLE = 45
RELEASE_CLOSE_ANGLE = 110
SERVO_SETTLE_S = 0.8
RELEASE_HOLD_S = 1.0

# Bin angle mapping
BIN_ANGLES = {
    "Plastic": 30,
    "Paper": 90,
    "Metal": 150,
    "General Waste": 0,
}

# =========================
# AI Model
# =========================
MODEL_PATH = "models/mobilenet_v3_dynamic_int8.tflite"
LABELS = ["Metal", "Paper", "Plastic", "General Waste"]
INPUT_SIZE = (224, 224)
CONFIDENCE_THRESHOLD = 0.50
TEMPERATURE = 0.7

# Optional fallback label if model confidence is too low
UNKNOWN_FALLBACK_LABEL = "General Waste"