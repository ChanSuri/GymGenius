# Temperature Optimization Service for Gym HVAC Control

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Temperature Optimization Service** is a microservice designed to manage and control the HVAC system of a gym. The service uses MQTT to receive real-time environmental data (temperature and humidity) and occupancy status, and then makes decisions on whether to turn the HVAC system on or off based on predefined temperature thresholds, gym schedule, and occupancy.

## Features
- **MQTT Integration**: Subscribes to environmental and occupancy data, and updates HVAC control commands based on the incoming data.
- **Threshold Management**: Dynamically updates temperature thresholds through MQTT messages.
- **Gym Schedule Awareness**: Controls HVAC based on the gym's opening hours, including pre-conditioning the environment before opening and shutting down when unoccupied before closing.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `requests` library

## Usage

### Service Registration
The service registers itself at startup by calling the `register_service` function.

he service will connect to the MQTT broker and begin monitoring temperature, humidity, and gym occupancy. It will also respond to HVAC control commands from administrators. The service also publishes actuation command based on its data analysis.




## MQTT Topics

### Subscribed Topics
- **Environment Data (`gym/environment`)**:
- Device connector publishes temperature and humidity data in JSON format.
- Example payload:
  \```json
  {
    "bn": "gym/environment",
    "e":[
      {"n": "temperature",
       "u": "Cel",
       "t":current_time,
       "v": temperature_value},
      {"n": "humidity",
       "u": "%",
       "t" :current_time,
       "v": humidity_value
      } 
    ]
  }
  \```

- **Threshold Update (`gym/desired_temperature`)**:
- Allows updates to the desired temperature, and the service calculates the upper and lower thresholds.
- Example payload:
  \```json
  {
    "topic": "gym/desired_temperature",
    "message": {
      "device_id": "admin_id",
      "timestamp": ""YYYY-MM-DD HH:MM:SS"",
      "data": {
        "desired_temperature": value,
        "unit": Celsius
      }
    }
  }  
  \```

- **Occupancy Data (`gym/occupancy/current`)**:
- Occupancy publishes the current occupancy of the gym.
- Example payload:
  \```json
  {
    "topic": "gym/occupancy/current",
    "message": {
      "device_id": "DviceConnector",
      "timestamp": "YYYY-MM-DD HH:MM:SS",
      "data": {
        "current_occupancy": value,
        "unit": count
      }
    }
  }  
  \```

- **HVAC On/Off Control by Administrator (`gym/hvac/on_of`)**:
- Allows the administrator to manually enable or disable HVAC control.
- Example payload:
  \```json
  {
    "topic": "gym/desired_temperature",
    "message": {
      "device_id": "admin_id",
      "timestamp": ""YYYY-MM-DD HH:MM:SS"",
      "data": {
        "state": "OFF"
      }
    }
  } 
  \``

### Published Topics
- **HVAC Control (`gym/hvac/control`)**:
- The service publishes commands to this topic to turn the HVAC system on or off and its set the mode (cool/heat).
- Example payload:
  \```json
  {
    "topic": "gym/hvac/control",
    "message": {
      "device_id": "Temperature optiimization and energy efficiency block",
      "timestamp": ""YYYY-MM-DD HH:MM:SS"",
      "data": {
        "control_command": "turn_on",
        "mode": "cool"
      }
    }
  }  
  \```
`
- **Alert Messages (`gym/environment/alert`)**:
- The service publishes alerts when temperature or humidity exceeds alert thresholds.
- Example payload:
  \```json
  {
    "topic": "gym/environment/alert",
    "message": {
      "device_id": "Temperature optiimization and energy efficiency block",
      "timestamp": ""YYYY-MM-DD HH:MM:SS"",
      "data": {
        "alert": "ALERT: Temperature too high! Current temperature: 36°C"
      }
    }
  }  
  \```

## Service Configuration
The service configuration includes MQTT broker details, gym schedule, and default thresholds.

- **MQTT Broker**: `test.mosquitto.org` on port `1883`.
- **Gym Schedule**: 
  - Open: 08:00 AM
  - Close: 12:00 AM (Midnight)
- **Default Thresholds**:
  - Upper Threshold: 28°C
  - Lower Threshold: 24°C

## Shutdown and Cleanup
To stop the service gracefully, press `Ctrl+C`. The signal handler will:
- Deregister the service from the service catalog using `delete_service()`.
- Stop the MQTT client loop cleanly.

