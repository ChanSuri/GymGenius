# Machine Availability Management Service

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
The **Machine Availability Management Service** is a microservice designed to monitor and manage the availability of gym machines. It uses MQTT to receive real-time updates on machine usage and provides a RESTful API to check the current status of all machines. The service aggregates machine data and saves it to a JSON file for persistence.

## Features
- **MQTT Integration**: Subscribes to topics related to machine availability and updates the status based on incoming data.
- **Machine Availability Tracking**: Keeps track of the number of available and occupied machines for each type.
- **Data Persistence**: Saves the current machine availability status to a JSON file.
- **REST API**: Provides an endpoint to retrieve the current machine availability status.

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
You can interact with the service's REST API at `http://localhost:8085/machine_availability` to retrieve the current status of all gym machines.

## MQTT Topics

### Machine Availability (`gym/availability/#`)
- The service subscribes to all machine availability topics under the `gym/availability/` namespace.
- Example topic structure: `gym/availability/treadmill/1`, `gym/availability/elliptical_trainer/2`, etc.
- Example payload:
  \```json
  {
    "e": [
      {"v": 1}
    ]
  }
  \```
  - **v**: Represents the machine availability status. `1` means the machine is occupied, `0` means the machine is available.

## REST API
The service provides a REST API to retrieve the current availability status of all machines.

- **Endpoint**: `/machine_availability`
- **Method**: GET
- **Response**:
  \```json
  {
    "status": "success",
    "time": "YYYY-MM-DD HH:MM:SS"
    "machines": {
        "treadmill": {
            "total": 5,
            "available": 3,
            "occupied": 2
        },
        "elliptical_trainer": {
            "total": 4,
            "available": 4,
            "occupied": 0
        },
        ...
    }
  }
  \```

## Service Configuration
The service configuration includes MQTT broker details and the machine types available in the gym.

- **MQTT Broker**: `test.mosquitto.org` on port `1883`.
- **Machine Types**:
  - Treadmill: 5 units
  - Elliptical Trainer: 4 units
  - Stationary Bike: 6 units
  - Rowing Machine: 3 units
  - Cable Machine: 5 units
  - Leg Press Machine: 5 units
  - Smith Machine: 5 units
  - Lat Pulldown Machine: 5 units

## Shutdown and Cleanup
When the service is stopped the signal handler will ensure that the MQTT client disconnects cleanly and the service is properly stopped.
