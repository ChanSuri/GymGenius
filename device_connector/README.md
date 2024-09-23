# Device Connector for Gym Management

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Device Connector Service** is a microservice designed to manage and integrate various gym devices, such as sensors and HVAC systems. It connects to an MQTT broker to exchange messages regarding environment data, machine availability, and occupancy. It also ensures that devices are registered and monitored in the Resource Catalog, and inactive devices are removed if they have not sent updates in a while.

## Features
- **Device Registration**: Registers devices (e.g., sensors, HVAC systems) with the Resource Catalog.
- **MQTT Integration**: Subscribes to and publishes messages on various MQTT topics related to occupancy, environment, and machine availability.
- **HVAC Control**: Automatically controls the HVAC system based on incoming MQTT commands and environment data.
- **Device Inactivity Management**: Checks for inactive devices and deletes them from the Resource Catalog if they have been inactive for more than 3 days.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `cherrypy` library
- `requests` library

## Usage

### Service Registration
The service registers devices with the Resource Catalog at startup by using the `register_device` function. This ensures that each device (e.g., environment sensor, occupancy sensor) is recognized and its data can be tracked.

The service will connect to the MQTT broker and the Resource Catalog, handle HVAC control, and ensure that machine availability and environment data are published to the appropriate MQTT topics.

## MQTT Topics

### Subscribed Topics
- **HVAC Control (`gym/hvac/control/#`)**: Receives commands to control HVAC for each room (e.g., turn on, turn off, set mode).
  Example payload:
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

- **HVAC On/Off (`gym/hvac/on_off/#`)**: Receives administrator commands to turn the HVAC on or off for each room.
  Example payload:
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

### Published Topics
- **Occupancy Entry (`gym/occupancy/entry`)**: Publishes entry events when a person enters the gym.
  Example payload:
  \```json
  {
    "bn": "gym/occupancy/entry",
    "e":{ "n": "entry",
          "u": "count",
          "t": timestamp,
          "v": value
        }  
  }
  \```

- **Occupancy Exit (`gym/occupancy/exit`)**: Publishes exit events when a person leaves the gym.
  Example payload:
  \```json
  {
    "bn": "gym/occupancy/exit",
    "e":{ "n": "exit",
          "u": "count",
          "t": timestamp,
          "v": value
        }  
  }
  \```

- **Environment Data (`gym/environment/{room_name}`)**: Publishes temperature and humidity data from the environment sensors.
  Example payload:
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

- **Machine Availability (`gym/availability/<machine_type>`)**: Publishes machine availability data for different types of machines (e.g., treadmills, stationary bikes).
  Example payload:
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

## Service Configuration
The service is configured to interact with an MQTT broker (`test.mosquitto.org` by default) and a **Resource Catalog** (by default at `http://localhost:8081/devices`).

- **MQTT Broker**: The broker can be configured by updating the `mqtt_broker` variable in the code.
- **Resource Catalog URL**: The URL for the Resource Catalog can be updated by modifying the `RESOURCE_CATALOG_URL` variable.

## Shutdown and Cleanup
To stop the service gracefully, press `Ctrl+C`. The signal handler will:
- Stop the MQTT client loop cleanly.
- Ensure all processes are properly terminated.
