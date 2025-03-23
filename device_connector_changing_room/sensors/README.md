
# Gym Device Simulation Services

## 📖 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Class Descriptions](#class-descriptions)
- [Simulation Examples](#simulation-examples)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## ✅ Overview
This project simulates gym devices to monitor:
- **Entry/Exit flows** through buttons
- **Environmental conditions** (Temperature/Humidity)
- **Machine availability** with PIR sensors

Each class generates data in **SenML** format ready to be sent to an IoT platform.

## Features
- Realistic simulation of:
  - People flow (entry/exit button)
  - Environmental data (DHT11)
  - Machine occupancy (PIR)
- Data output structured in JSON SenML format
- Option to define simulation duration or run a single event

## Installation
### Requirements
- Python 3.x
- No external libraries required for simulation

### Running individual modules
```bash
python3 button_class.py
python3 dht11_class.py
python3 PIR_class.py
```

## Usage
Each file is executable and will prompt the user for simulation parameters:
- **Duration of the simulation**
- **Room or area to simulate**
- **Machine type (for PIR)**
- **Number of machines to monitor (for PIR)**

## Class Descriptions

### `SimulatedButtonSensor` (`button_class.py`)
Simulates gym entrance and exit counts.
- Main attributes: `entrance_count`, `exit_count`
- Generates SenML events with fields:
  - `device_id`, `event_type`, `location`, `senml_record`
- Supports time-based or single event simulation

---

### `SimulatedDHT11Sensor` (`dht11_class.py`)
Simulates environmental readings of temperature and humidity in different rooms.
- Simulated rooms: `entrance`, `cardio_room`, `lifting_room`, `changing_room`
- Values fluctuate within realistic thresholds
- SenML output with `temperature` and `humidity` event arrays

---

### `SimulatedPIRSensor` (`PIR_class.py`)
Simulates the availability of cardio and weight machines.
- Simulated cardio machines: treadmill, bike, etc.
- Simulated weight machines: cable machine, leg press, smith machine, etc.
- SenML events with binary state (occupied/free)

---

## Simulation Examples
Each class can be executed with:

Example output:
```json
{
  "device_id": "EntranceSensor001",
  "event_type": "entry",
  "type": "push-button-enter",
  "location": "entrance",
  "status": "active",
  "endpoint": "GymGenius/Occupancy/Entrance",
  "time": "2025-03-21 15:30:00",
  "senml_record": {
    "bn": "GymGenius/Occupancy/Entrance",
    "bt": 1711037400,
    "n": "push-button-enter",
    "u": "count",
    "v": 1
  }
}
```

---

## Shutdown and Cleanup
- End the simulation using **CTRL+C**

---
