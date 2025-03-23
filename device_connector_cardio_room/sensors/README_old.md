# Gym Device Management Services

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [REST API](#rest-api)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The files **buutton.py**, **dht11.py**, and **PIR_sensor.py** consist of three main components designed to monitor occupancy, environmental conditions, and machine availability in a gym environment. They interact with a device connector to send and receive data from various sensors, including PIR sensors, DHT11 temperature and humidity sensors, and entrance/exit buttons. Moreover, they manage both real and simulated devices and can be deployed in a gym for real-time monitoring and data management. Hence, the measuraments are sent to the device connector through the employment of REST APIs. 

### Components
- **PIR_sensor.py**: Monitors machine availability using a real PIR sensor and simulates occupancy for other machines.
- **dht11.py**: Collects and sends temperature and humidity data using a real DHT11 sensor, while simulating data for other rooms.
- **button.py**: Tracks gym occupancy using a real button for entrance detection and simulates exit events.

## Features
- **Real and Simulated Sensor Management**: Each script handles real sensors (PIR, DHT11, entrance button) while also simulating data for other machines or rooms.
- **Data Sending**: Publishes data, including occupancy, availability, temperature, and humidity, to the device connector.
- **Simulated Machine Usage**: The scripts simulate machine usage for cardio and lifting rooms with realistic intervals and state changes.

## Installation

### Prerequisites
- Python 3.x
- `RPi.GPIO` (for Raspberry Pi GPIO control)
- `requests` library
- `adafruit_dht` (for DHT11 sensor)
- `board` library (for DHT11 sensor)

### Set up the hardware:
- **PIR_sensor.py**: Connect the PIR sensor to the Raspberry Pi using GPIO 17 (Pin 11).
- **dht11.py**: Connect the DHT11 sensor to the Raspberry Pi using GPIO 15 (Pin 10).
- **button.py**: Connect the entrance button to GPIO 23 (Pin 16).

## Usage

### Running the Services
You can run each service individually or in parallel.

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
  cardio_machines = ["treadmill_2", ... , "elliptical_trainer_1", ... ,  "stationary_bike_1", ... , "rowing_machine_1", ...]
  lifting_machines = ["cable_machine_1", ... , "leg_press_machine_1", ... ,"smith_machine_1", ... , "lat_pulldown_machine_1", ...]
  \```

### Example Configuration for `button.py`
- Real entrance button for gym occupancy: 
  \```python
  entrance_simulation = { "type": "real", "entry_count": 0} 
- Simulated exit button events: 
  \```python
  exit_simulation = { "type": "simulated", "exit_count": 0 } 
  \```

## REST API

Each script sends data to a device connector via HTTP POST requests. Below is an overview of the REST API endpoints used by the system:

### POST `/`
This endpoint is used to send sensor data to the device connector.

#### Example of request from `dht11.py`:
- URL: `http://localhost:8082`
- Method: `POST`
- Payload:
  ```json
  {
    "device_id": "DHT11_Sensor_entrance",
    "event_type": "environment",
    "type": "DHT11",
    "location": "entrance",
    "status": "active",
    "endpoint": "gym/environment/entrance",
    "time": "2024-09-23T12:34:56Z",
    "senml_record": {
      "bn": "gym/environment/entrance",
      "e": [
        {"n": "temperature", "u": "Cel", "t": "2024-09-23T12:34:56Z", "v": 22.5},
        {"n": "humidity", "u": "%", "t": "2024-09-23T12:34:56Z", "v": 50.0}
      ]
    }
  }

#### Example of request from`PIR_sensor.py`:
- URL: `http://localhost:8082`
- Method: `POST`
- Payload:
  ```json
  {
    "device_id": "PIR_treadmill_1",
    "event_type": "availability",
    "type": "PIR",
    "location": "cardio_room",
    "status": "active",
    "endpoint": "gym/occupancy/treadmill_1",
    "time": "2024-09-23T12:34:56Z",
    "senml_record": {
      "bn": "gym/occupancy/treadmill_1",
      "n": "treadmill_1",
      "u": "binary",
      "v": 1
    }
  }

#### Example of request from `button.py`:
- URL: `http://localhost:8082`
- Method: `POST`
- Example of payload for entrance:
  ```json
  {
    "device_id": "EntranceSensor001",
    "event_type": "entry",
    "type": "push-button-enter",
    "location": "entrance",
    "status": "active",
    "endpoint": "GymGenius/Occupancy/Entrance",
    "time": "2024-09-23T12:34:56Z",
    "senml_record": {
      "bn": "GymGenius/Occupancy/Entrance",
      "bt": 1695478496,
      "n": "push-button-enter",
      "u": "count",
      "v": 1
    }
  }

### Response:
For each request, a succesful response will give back:
```json
{
  "message": "Data received successfully",
  "status_code": 200
}
```

## Shutdown and Cleanup
To stop any of the scripts gracefully, press `Ctrl+C`. The services will:
- Stop reading data from sensors.
- Clean up GPIO states (for the Raspberry Pi scripts).
- Terminate any running threads and processes cleanly.

Make sure to run `GPIO.cleanup()` after stopping the scripts to release the GPIO pins properly.
