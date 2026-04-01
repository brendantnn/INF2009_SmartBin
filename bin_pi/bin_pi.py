import time
import json
import paho.mqtt.client as mqtt
from gpiozero import DistanceSensor

# ---------- CONFIG ----------
TRIGGER_DISTANCE_CM = 7
CHECK_DELAY = 1.0

# MQTT SETTINGS
MQTT_BROKER = "54.163.202.184"
MQTT_TOPIC = "waste/capacity"

# BIN CONFIGURATIONS
# Update the 'trig' and 'echo' values to match your actual Raspberry Pi wiring!
BINS = [
    # {"pi_id": "bin_01_carpark", "trig": 27, "echo": 17, "was_full": False},
    # {"pi_id": "bin_02_foodgle",   "trig": 22, "echo": 23, "was_full": False},
    # {"pi_id": "bin_03_library",   "trig": 24, "echo": 25, "was_full": False},
    {"pi_id": "bin_01_carpark", "trig": 5,  "echo": 6,  "was_full": False}
]
# ---------------------------

# Setup MQTT Client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

print("?? Connecting to MQTT Broker...")
try:
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start() 
    print("? Connected successfully.")
except Exception as e:
    print(f"? Could not connect to MQTT: {e}")

# Initialize Sensors dynamically and store them back in the BINS dictionary
print("?? Initializing sensors...")
for bin_data in BINS:
    bin_data["sensor"] = DistanceSensor(
        echo=bin_data["echo"], 
        trigger=bin_data["trig"], 
        max_distance=2.0
    )
    print(f"   -> Setup {bin_data['pi_id']} on Trig:{bin_data['trig']} Echo:{bin_data['echo']}")

def send_mqtt_alert(pi_id, is_full):
    # This payload now dynamically sends True or False for the specific bin
    payload = {
        "pi_id": pi_id,
        "needs_emptying": is_full
    }
    
    try:
        client.publish(MQTT_TOPIC, json.dumps(payload))
        status_text = "FULL ??" if is_full else "EMPTY ??"
        print(f"?? [MQTT SENT] {pi_id} | Status: {status_text} | Payload: {payload}")
    except Exception as e:
        print(f"? Failed to publish for {pi_id}: {e}")

print("?? Smart Bin Monitor Running...")

try:
    while True:
        # Loop through each bin configuration
        for bin_data in BINS:
            # Convert distance to CM
            distance_cm = round(bin_data["sensor"].distance * 100, 2)
            
            # Check if within 7cm trigger distance
            is_full = distance_cm <= TRIGGER_DISTANCE_CM

            # Logic: Detect whenever the state CHANGES for THIS specific bin
            if is_full != bin_data["was_full"]:
                if is_full:
                    print(f"\n[DETECTED] {bin_data['pi_id']} - Object at {distance_cm} cm (Threshold: {TRIGGER_DISTANCE_CM}cm)")
                else:
                    print(f"\n[CLEARED] {bin_data['pi_id']} - Sensor distance: {distance_cm} cm")
                
                # Send the current state (True or False) to the Dashboard
                send_mqtt_alert(bin_data["pi_id"], is_full)
                
                # Update the stored state for this specific bin
                bin_data["was_full"] = is_full
        
        # Wait before scanning all sensors again
        time.sleep(CHECK_DELAY)

except KeyboardInterrupt:
    print("\n?? Stopped.")
    client.loop_stop()
    client.disconnect()