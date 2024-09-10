# Temperature Optimization Service for Gym HVAC Control

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [REST API](#rest-api)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Temperature Optimization Service** is a microservice designed to manage and control the HVAC system of a gym. The service uses MQTT to receive real-time environmental data (temperature and humidity) and occupancy status, and then makes decisions on whether to turn the HVAC system on or off based on predefined temperature thresholds, gym schedule, and occupancy.

## Features
- **MQTT Integration**: Subscribes to environmental and occupancy data, and updates HVAC control commands based on the incoming data.
- **Threshold Management**: Dynamically updates temperature thresholds through MQTT messages.
- **Gym Schedule Awareness**: Controls HVAC based on the gym's opening hours, including pre-conditioning the environment before opening and shutting down when unoccupied before closing.
- **REST API**: Provides a RESTful API endpoint to check the current HVAC state, thresholds, and occupancy.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `cherrypy` library
- `requests` library

## Usage

### Service Registration
The service registers itself at startup by calling the `register_service` function.

### Interacting with the REST API
You can interact with the service's REST API at `http://localhost:8084/hvac` to retrieve the current HVAC status, thresholds, and occupancy.

## MQTT Topics

### Environment Data (`gym/environment`)
- Device connector publishes temperature and humidity data in JSON format.
- Example payload:
  \```json
  {
    "bn": "gym/environment"
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

### Threshold Update (`gym/threshold`)
- Allows updates to the upper and lower temperature thresholds.
- Example payload:
  \```json
  {
    "upper": 28,
    "lower": 22
  }
  \```

### Occupancy Data (`gym/occupancy/current`)
- Device connector publishes the current occupancy of the gym.
- Example payload:
  \```json
  {
    "occupancy": 10
  }
  \```

### HVAC Control (`gym/hvac/control`)
- The service publishes commands to this topic to turn the HVAC system on or off.
- Example payload:
  \```json
  {
    "command": "turn_on"
  }
  \```

## REST API
The service provides a REST API to retrieve the current status of the HVAC system.

- **Endpoint**: `/hvac`
- **Method**: GET
- **Response**:
  \```json
  {
    "status": "success",
    "time": "YYYY-MM-DD HH:MM:SS",
    "hvac_state": "off",
    "thresholds": {
      "upper": 28,
      "lower": 24
    },
    "occupancy": 0
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
When the service is stopped the signal handler will ensure that the MQTT client disconnects cleanly and the service is properly stopped.

