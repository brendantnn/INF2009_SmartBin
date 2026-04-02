# INF2009 SmartBin by Group 5
Members:
Chew Kim Hong, Devyn (2302144)
Goh See Leng (2302016)
Tan Sheng Le Brendan (2301782)
Chew Ruixuan (2302036)
Yong Yu Hao Ryan (2301805)

SmartBin is a multi-part smart waste sorting and monitoring system built around Raspberry Pi 5 devices and a web dashboard.

The repository is split into three main parts:

- `main_pi/`: runs on the Raspberry Pi 5 that detects incoming waste, captures an image, classifies the item with a TensorFlow Lite model, and moves the trash to the correct bin using servos.
- `bin_pi/`: runs on the Raspberry Pi 5 attached to the physical bins. It checks whether a bin is full with ultrasonic sensors and publishes the status to an MQTT broker.
- `dashboard/`: a Next.js dashboard for viewing live bin status and recent AI classification history.

## System Overview

At a high level, the system works like this:

1. A user places an item into the smart bin intake.
2. `main_pi` detects the item with an ultrasonic sensor.
3. The Pi captures an image with a webcam.
4. A TensorFlow Lite model classifies the item as one of:
   - `Plastic`
   - `Paper`
   - `Metal`
   - `General Waste`
5. The selector servo rotates to the matching bin position.
6. The release servo opens and drops the item into the selected bin.
7. `bin_pi` monitors the fill level of each bin and publishes `needs_emptying` updates over MQTT.
8. The dashboard reads device status and prediction logs from a PostgreSQL database and displays them for operators.

## Repository Structure

```text
.
|-- bin_pi/
|   |-- bin_pi.py
|   `-- requirements.txt
|-- main_pi/
|   |-- ai/
|   |-- controllers/
|   |-- models/
|   |-- config.py
|   |-- main.py
|   `-- requirements.txt
|-- dashboard/
|   |-- app/
|   |-- prisma/
|   |-- package.json
|   `-- ...
`-- README.md
```

## Component Details

### `main_pi`

This service is the AI sorting controller. Based on the current code, it uses:

- an ultrasonic sensor to detect when an object is present
- a webcam to capture an image of the item
- a TensorFlow Lite model at `main_pi/models/mobilenet_v3_dynamic_int8.tflite`
- one servo for bin selection
- one servo for the release platform or trapdoor

Key files:

- `main_pi/main.py`: main control loop
- `main_pi/config.py`: GPIO pins, servo angles, model settings, and timing thresholds
- `main_pi/ai/classifier.py`: TFLite image classification
- `main_pi/controllers/`: hardware controller classes for ultrasonic, webcam, and servo control

Current class labels configured in code:

- `Metal`
- `Paper`
- `Plastic`
- `General Waste`

Default bin angle mapping in `main_pi/config.py`:

- `Plastic -> 30`
- `Paper -> 90`
- `Metal -> 150`
- `General Waste -> 0`

### `bin_pi`

This service monitors whether bins are full and pushes updates to MQTT.

Based on the current implementation:

- each monitored bin is configured in the `BINS` list inside `bin_pi/bin_pi.py`
- each bin uses an ultrasonic distance sensor
- when the measured distance crosses the fullness threshold, the Pi publishes a JSON payload to MQTT

Current MQTT payload format:

```json
{
  "pi_id": "bin_01_carpark",
  "needs_emptying": true
}
```

Current MQTT settings in code:

- broker: `54.163.202.184`
- topic: `waste/capacity`

### `dashboard`

The dashboard is a Next.js application backed by Prisma and PostgreSQL.

It currently provides:

- a main dashboard page showing all bins and whether they need emptying
- a recent AI classifications table with image, material, confidence, and timestamp
- a per-bin detail page showing that bin's classification history

Important files:

- `dashboard/app/page.tsx`: main dashboard page
- `dashboard/app/bin/[id]/page.tsx`: per-bin detail page
- `dashboard/prisma/schema.prisma`: database schema

Current Prisma models:

- `Device`
  - `pi_id`
  - `location`
  - `needs_emptying`
  - `last_seen`
- `Prediction`
  - `id`
  - `pi_id`
  - `waste_class`
  - `confidence`
  - `s3_url`
  - `timestamp`

## Setup

### 1. `main_pi` setup

Create a Python environment on the Raspberry Pi and install dependencies:

```bash
cd main_pi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the sorter:

```bash
python main.py
```

Before running on hardware, review and update:

- GPIO pins in `main_pi/config.py`
- servo angles in `main_pi/config.py`
- camera index in `main_pi/config.py`
- trigger distances and timing thresholds in `main_pi/config.py`

### 2. `bin_pi` setup

Create a Python environment on the Raspberry Pi and install dependencies:

```bash
cd bin_pi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the bin monitor:

```bash
python bin_pi.py
```

Before running on hardware, review and update:

- `BINS` sensor pin mappings in `bin_pi/bin_pi.py`
- `TRIGGER_DISTANCE_CM` in `bin_pi/bin_pi.py`
- MQTT broker and topic in `bin_pi/bin_pi.py`

### 3. `dashboard` setup

Install dependencies:

```bash
cd dashboard
npm install
```

Create a `.env` file with a PostgreSQL connection string:

```bash
DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DATABASE"
```

Apply the Prisma schema:

```bash
npx prisma generate
npx prisma db push
```

Start the dashboard locally:

```bash
npm run dev
```

Then open `http://localhost:3000`.

## Integration Notes

This repository currently shows:

- local AI sorting logic on `main_pi`
- MQTT-based fullness reporting on `bin_pi`
- dashboard read access to device and prediction data through PostgreSQL

What is not currently present in this repository:

- the service that consumes MQTT messages and writes bin status into the dashboard database
- the service that uploads captured images and AI predictions into the `Prediction` table
- deployment scripts or production infrastructure configuration

If those integrations exist in your final system, they are external to this repository and should be documented separately or added later.

## Hardware Notes

The code indicates that the project targets Raspberry Pi 5 hardware and uses:

- ultrasonic distance sensors
- a USB or CSI camera exposed through OpenCV
- servo motors controlled through GPIO

For Raspberry Pi 5, the servo controller forces `gpiozero` to use the `lgpio` backend.

## Demo Flow

1. Start `main_pi` on the AI sorting Raspberry Pi.
2. Start `bin_pi` on the monitoring Raspberry Pi.
3. Ensure the MQTT broker and database-backed dashboard services are reachable.
4. Open the dashboard.
5. Insert waste into the intake.
6. Verify the item is classified and routed correctly.
7. Fill a monitored bin close to the threshold and verify the dashboard reflects `needs_emptying`.

## Notes

- Captured images from `main_pi` are saved to the `captures/` folder by default.
- The classifier falls back to `General Waste` when confidence is below the configured threshold.
- The dashboard currently polls fresh data using Next.js revalidation every 5 seconds.
