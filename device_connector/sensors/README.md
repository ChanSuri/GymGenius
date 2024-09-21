# Gym Device Management Services

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Gym Device Management Services** consist of three main components designed to monitor occupancy, environmental conditions, and machine availability in a gym environment. These services interact with a device connector to send and receive data from various sensors, including PIR sensors, DHT11 temperature and humidity sensors, and entrance/exit buttons. The services manage both real and simulated devices and can be deployed in a gym for real-time monitoring and data management.

### Components
- **PIR_sensor.py**: Monitors machine availability using a real PIR sensor and simulates occupancy for other machines.
- **dht11.py**: Collects and sends temperature and humidity data using a real DHT11 sensor, while simulating data for other rooms.
- **button.py**: Tracks gym occupancy using a real button for entrance detection and simulates exit events.

## Features
- **Real and Simulated Sensor Management**: Each script handles real sensors (PIR, DHT11, entrance button) while also simulating data for other machines or rooms.
- **Device Registration**: Automatically registers devices with the device connector and updates their status.
- **Data Sending**: Publishes data, including occupancy, availability, temperature, and humidity, to the device connector.
- **Simulated Machine Usage**: The scripts simulate machine usage for cardio and lifting rooms with realistic intervals and state changes.

## Installation

### Prerequisites
- Python 3.x
- `RPi.GPIO` (for Raspberry Pi GPIO control)
- `requests` library
- `adafruit_dht` (for DHT11 sensor)
- `board` library (for DHT11 sensor)

### Steps
1. Clone the repository:
   \```bash
   git clone https://your-repository-url.git
   cd your-repository
   \```

2. Install the required Python packages:
   \```bash
   pip install RPi.GPIO requests adafruit-circuitpython-dht board
   \```

3. Set up the hardware:
   - **PIR_sensor.py**: Connect the PIR sensor to the Raspberry Pi using GPIO 17 (Pin 11).
   - **dht11.py**: Connect the DHT11 sensor to the Raspberry Pi using GPIO 15 (Pin 10).
   - **button.py**: Connect the entrance button to GPIO 23 (Pin 16).

## Usage

### Running the Services
You can run each service individually or in parallel.

- **PIR Sensor and Machine Simulation** (`PIR_sensor.py`):
  \```bash
  python PIR_sensor.py
  \```
  This script monitors a real PIR sensor for the treadmill in the cardio room and simulates machine usage for other cardio and lifting room machines.

- **DHT11 Sensor and Environment Monitoring** (`dht11.py`):
  \```bash
  python dht11.py
  \```
  This script collects real-time temperature and humidity data from the entrance and simulates data for other rooms (e.g., cardio room, lifting room, changing room).

- **Entrance Button Monitoring** (`button.py`):
  \```bash
  python button.py
  \```
  This script tracks real-time button presses for gym entry and simulates exit events after random intervals.

## Service Configuration
Each script is configured to send data to a device connector located at `http://localhost:8082`. The configuration includes device IDs, sensor types, and room names, which can be modified based on your setup.

### Example Configuration for `dht11.py`
- Real sensor (DHT11) in the entrance:
  \```python
  rooms = {
    "entrance": {"type": "real", "temperature": None, "humidity": None},
    ...
  }
  \```
- Simulated temperature and humidity for other rooms:
  \```python
  rooms = {
    "cardio_room": {"type": "simulated", "temperature": 22.0, "humidity": 50.0},
    "lifting_room": {"type": "simulated", "temperature": 23.0, "humidity": 52.0},
    "changing_room": {"type": "simulated", "temperature": 24.0, "humidity": 55.0}
  }
  \```

### Example Configuration for `PIR_sensor.py`
- Real PIR sensor for treadmill 1:
  \```python
  device_id_real = "PIR_treadmill_1"
  \```
- Simulated machines in cardio and lifting rooms:
  \```python
  cardio_machines = ["treadmill", "elliptical_trainer", "stationary_bike"]
  lifting_machines = ["rowing_machine", "cable_machine", "leg_press_machine", "smith_machine", "lat_pulldown_machine"]
  \```

## Shutdown and Cleanup
To stop any of the scripts gracefully, press `Ctrl+C`. The services will:
- Stop reading data from sensors.
- Clean up GPIO states (for the Raspberry Pi scripts).
- Terminate any running threads and processes cleanly.

Make sure to run `GPIO.cleanup()` after stopping the scripts to release the GPIO pins properly.
