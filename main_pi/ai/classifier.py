import time
import numpy as np
import cv2

from config import (
    MODEL_PATH,
    LABELS,
    INPUT_SIZE,
    CONFIDENCE_THRESHOLD,
    TEMPERATURE,
    UNKNOWN_FALLBACK_LABEL,
)


class WasteClassifier:
    def __init__(self):
        self.interpreter = None
        self.input_details = None
        self.output_details = None

        # Try ai_edge_litert first
        try:
            from ai_edge_litert.interpreter import Interpreter
            print("[AI] Using ai_edge_litert Interpreter")
            self.interpreter = Interpreter(model_path=MODEL_PATH)
        except Exception:
            try:
                from tflite_runtime.interpreter import Interpreter
                print("[AI] Using tflite_runtime Interpreter")
                self.interpreter = Interpreter(model_path=MODEL_PATH)
            except Exception:
                try:
                    import tensorflow as tf
                    print("[AI] Using tensorflow.lite Interpreter")
                    self.interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
                except Exception as e:
                    raise RuntimeError(
                        "No compatible TFLite interpreter found. "
                        "Install ai-edge-litert, tflite-runtime, or tensorflow."
                    ) from e

        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        print(f"[AI] Model loaded: {MODEL_PATH}")
        print(f"[AI] Labels: {LABELS}")

    def preprocess(self, image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, INPUT_SIZE)
        img = img.astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)

        input_dtype = self.input_details[0]["dtype"]
        if input_dtype == np.uint8:
            # Quantized model input
            scale, zero_point = self.input_details[0]["quantization"]
            if scale > 0:
                img = img / scale + zero_point
            img = np.clip(img, 0, 255).astype(np.uint8)
        else:
            img = img.astype(input_dtype)

        return img

    @staticmethod
    def softmax(logits, temperature=1.0):
        logits = np.asarray(logits, dtype=np.float32)
        logits = logits / max(temperature, 1e-6)
        logits = logits - np.max(logits)
        exp_vals = np.exp(logits)
        return exp_vals / np.sum(exp_vals)

    def classify_image(self, image_path: str):
        input_data = self.preprocess(image_path)

        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)

        start = time.perf_counter()
        self.interpreter.invoke()
        end = time.perf_counter()

        latency_ms = (end - start) * 1000.0

        output = self.interpreter.get_tensor(self.output_details[0]["index"])[0]
        output = np.array(output)

        output_dtype = self.output_details[0]["dtype"]
        if output_dtype == np.uint8:
            scale, zero_point = self.output_details[0]["quantization"]
            if scale > 0:
                output = scale * (output.astype(np.float32) - zero_point)

        probs = self.softmax(output, temperature=TEMPERATURE)
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])

        label = LABELS[pred_idx] if pred_idx < len(LABELS) else UNKNOWN_FALLBACK_LABEL

        if confidence < CONFIDENCE_THRESHOLD:
            label = UNKNOWN_FALLBACK_LABEL

        return label, confidence, latency_ms