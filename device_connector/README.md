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
- **Dynamic Room Configuration**: Retrieves room information dynamically from the Service Catalog, eliminating static configuration files.
- **Device Registration**: Registers devices (e.g., sensors, HVAC systems) with the Resource Catalog.
- **MQTT Integration**: Subscribes to and publishes messages on various MQTT topics related to occupancy, environment, and machine availability.
- **HVAC Control**: Automatically controls the HVAC system based on incoming MQTT commands and environment data.
- **Temperature Simulation**: Adjusts and simulates the temperature for each room, considering HVAC activity and gradual changes.
- **Device Inactivity Management**: Checks for inactive devices and deletes them from the Resource Catalog if they have been inactive for more than 3 days.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `cherrypy` library
- `requests` library

## Usage

### Service Initialization
The service initializes by:
1. Loading configuration from a `config.json` file.
2. Retrieving **MQTT broker** and **port information** from the **Service Catalog**.
3. Retrieving **room configurations** from the **Service Catalog**.
4. Registering the service in the **Resource Catalog** using the `register_service` function.
5. Connecting to the MQTT broker.
6. Subscribing to various topics for machine availability, HVAC control, and entry/exit events.
7. Performing device checks at startup to delete inactive devices.

### Device Registration
The service registers devices with the Resource Catalog at startup using the `register_device` function. This ensures that each device (e.g., environment sensor, occupancy sensor) is recognized and its data can be tracked. If a device is successfully registered or updated, it will then start publishing relevant data.

### Device Inactivity Management
The service periodically checks the **Resource Catalog** for devices that have not been updated in the last 3 days. If such devices are found, they are deleted from the catalog.

### MQTT Message Handling
The service subscribes to topics related to HVAC control, machine availability, and occupancy entry/exit events. Based on incoming messages, it:
- Controls HVAC systems, adjusting the mode and on/off state for specific rooms.
- Publishes availability data for machines like treadmills and stationary bikes.
- Publishes environment data such as temperature and humidity, while considering HVAC effects.
  
### Temperature Simulation
The service simulates temperature changes in each room by applying HVAC effects or gradually returning the temperature to real values when HVAC is off.

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
The service is configured via a `config.json` file. The configuration includes settings for:

- **Service Catalog URL**: The URL of the Service Catalog from which the service retrieves the MQTT broker, port, and room configurations. By default, it is set to `http://service_catalog:8080` and `http://localhost:8081/devices`, respectively.
- **Service Catalog URL**: The URL of the Resource Catalog where devices are registered. By default, it is set to `http://localhost:8081/devices`
- **Subscribed Topics**: Lists MQTT topics the service listens to (e.g., HVAC control).
- **Published Topics**: Specifies the topics to publish data (e.g., environment data, machine availability).

## Shutdown and Cleanup
To stop the service gracefully, press `Ctrl+C`. The signal handler will:
- Stop the MQTT client loop cleanly.
- Ensure all processes are properly terminated.
- Delete the service from the **Service Catalog** by calling the `delete_service` function.
