# Machine Availability Service

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Machine Availability Service** is a microservice that monitors and manages the availability of gym machines. It listens to MQTT topics for real-time machine availability updates, maintains the current status of each machine type (available/occupied), and publishes aggregated data to a dedicated MQTT topic. The service uses MQTT to receive and publish data and can be configured for various machine types.

## Features
- **MQTT Integration**: Subscribes to machine availability topics and updates the machine status accordingly.
- **Real-time Machine Monitoring**: Tracks the availability and occupancy of each machine type.
- **Data Publishing**: Publishes machine availability data to aggregated MQTT topics.
- **Service Registration**: Registers and deregisters the service with a service catalog at startup and shutdown.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library

## Usage

### Service Registration
The service registers itself at startup by calling the `register_service` function.

The service will connect to the MQTT broker and begin listening for machine availability updates. The current machine availability status will be published to the MQTT topics.

## MQTT Topics

### Subscribed Topics
- **Machine Availability (`gym/availability/#`)**: 
  - Subscribes to all machine availability topics. 
  - Each topic represents a specific machine type and instance, for example:
    \```bash
    gym/availability/treadmill/1
    gym/availability/elliptical_trainer/2
    \```
  - Expected payload format:
    \```json
    {
    "bn": "gym/availability/treadmill/1",
    "e":{ "n": "treadmill_availability",
          "u": "binary",
          "t": current_time,
          "v": 0
        }  
    }
    \```
  - If the "v" field is 0 if the machine is available, instead if it is 1 the machine is occupied

### Published Topics
- **Aggregated Machine Availability (`gym/group_availability/<machine_type>`)**: 
  - Publishes aggregated availability data for each machine type.
  - Example topic: `gym/group_availability/treadmill`
  - Payload format:
    \```json
    {
      "topic": "gym/group_availability/treadmill",
      "message": {
        "device_id": "Machine availability block",
        "timestamp": "YYYY-MM-DD HH:MM:SS",
        "data": {
          "available": 3,
          "busy": 2,
          "total": 5,
          "unit": "count"
        }
      }
    }
    \```

## Service Configuration
The service configuration includes MQTT broker details, gym schedule, and default thresholds.

- **MQTT Broker**: `test.mosquitto.org` on port `1883`.
- Example machine types configuration:
  \```python
  machine_types = {
      "treadmill": 5,
      "elliptical_trainer": 4,
      "stationary_bike": 6,
      "rowing_machine": 3,
      "cable_machine": 5,
      "leg_press_machine": 5,
      "smith_machine": 5,
      "lat_pulldown_machine": 5
  }
  \```

## Shutdown and Cleanup
To stop the service gracefully, press `Ctrl+C`. The signal handler will:
- Deregister the service from the service catalog using `delete_service()`.
- Stop the MQTT client loop cleanly.