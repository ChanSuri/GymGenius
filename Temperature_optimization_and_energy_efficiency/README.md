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
The **Temperature Optimization Service** is a microservice designed to manage and control the HVAC system of a gym. The service uses MQTT to receive real-time environmental data (temperature and humidity), occupancy status, and administrator commands, and then makes decisions on whether to turn the HVAC system on or off based on predefined temperature thresholds, gym schedule, and occupancy. It also features manual and automatic HVAC control modes with hysteresis to prevent frequent toggling.

All information related to MQTT broker, temperature thresholds, and alert limits are dynamically retrieved from the service catalog via a GET request. The configuration file only contains the service catalog URL and MQTT topics to subscribe to.

## Features
- **Dynamic Configuration**: The MQTT broker details, temperature thresholds, and alert limits, and gym schedule are fetched dynamically from the service catalog.
- **MQTT Integration**: Subscribes to environmental data, occupancy updates, and administrator commands, and publishes HVAC control decisions.
- **Threshold Management with Hysteresis**: Dynamically updates temperature thresholds through MQTT messages, prevents frequent toggling using a hysteresis approach, and alerts when conditions exceed predefined limits.
- **Gym Schedule Awareness**: Controls HVAC based on the gym's opening hours, including pre-conditioning the environment before opening and shutting down when unoccupied before closing.
- **Manual & Automatic Control Modes**: Allows the administrator to override automatic HVAC control and set specific modes (cool/heat) or revert back to automatic.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `requests` library

## Usage

### Service Registration
At startup, the service registers itself with the service catalog using the `register_service` function from `registration_functions.py`.

## Dynamic Configuration from the Service Catalog
At startup, the service retrieves the following information from the service catalog via a GET request:
- **MQTT Broker and Port**: The service dynamically fetches the broker IP and port.
- **Temperature Thresholds**: The default temperature thresholds (upper and lower bounds) are retrieved for each room.
- **Alert Limits**: The service retrieves the alert limits for temperature and humidity for each room.
- **Gym Schedule**: The opening and closing times of the gym are dynamically fetched and used for HVAC control.

The service will connect to the MQTT broker and begin monitoring temperature, humidity, and gym occupancy. It will also respond to HVAC control commands from administrators. Moreover, thes service publishes actuation command based on its data analysis.


## MQTT Topics

### Subscribed Topics
- **Environment Data (`gym/environment/#`)**:
- Device connector publishes temperature and humidity data of a specific room in JSON format.
- Example payload:
  \```json
  {
    "bn": "gym/environment/{room_name}",
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

- **Threshold Update (`gym/desired_temperature/#`)**:
- Allows updates to the desired temperature of a specific room, and the service calculates the upper and lower thresholds.
- Example payload:
  \```json
  {
    "topic": "gym/desired_temperature/{room_name}",
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

- **HVAC On/Off Control by Administrator (`gym/hvac/on_off/#`)**:
- Allows the administrator to manually turn ON/OFF the HVAC (setting the mode cool/heat) or use the AUTO command (setting the mode as None) to set automatic HVAC control.
- Example payload:
  \```json
  {
    "topic": "gym/hvac/on_off/{room_name}",
    "message": {
      "device_id": "admin_id",
      "timestamp": ""YYYY-MM-DD HH:MM:SS"",
      "data": {
        "state": "ON"
        "mode": "cool"
      }
    }
  } 
  \```
- The state can be ON/OFF/AUTO and the mode can be cool/heat/None (None is used when OFF or AUTO)

### Published Topics
- **HVAC Control (`gym/hvac/control/{room_name}`)**:
- The service publishes commands to this topic to turn the HVAC system of a specific room on or off and its set the mode (cool/heat).
- Example payload:
  \```json
  {
    "topic": "gym/hvac/control/{room_name}",
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
- **Alert Messages (`gym/environment/alert/{room_name}`)**:
- The service publishes alerts when temperature or humidity of a specific room exceeds alert thresholds.
- Example payload:
  \```json
  {
    "topic": "gym/environment/alert/{room_name}",
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
The service configuration is dynamically fetched from the Service Catalog. The configuration includes:
- **MQTT Broker Details**: The broker IP and port are retrieved via a GET request.
- **Temperature and Humidity Thresholds**: The service retrieves the default thresholds for temperature and humidity from the service catalog.
- **Gym Schedule**: The opening and closing times of the gym are dynamically fetched from the service catalog.

The only manual configuration required in the `config.json` file is:
  - **Service Catalog URL**: The URL of the service catalog from which the service retrieves the necessary information.
  - **MQTT Topics**: The topics to which the service subscribes and publishes.

## Shutdown and Cleanup
To stop the service gracefully, press `Ctrl+C`. The signal handler will:
- Deregister the service from the service catalog using the `delete_service` function..
- Stop the MQTT client loop cleanly.

