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
The **Machine Availability Service** is a microservice that monitors and manages the availability of gym machines. It listens to MQTT topics for real-time machine availability updates, maintains the current status of each machine type (available/occupied), and publishes aggregated data to a dedicated MQTT topic. The service uses MQTT to receive and publish data and can be configured for various machine types. Additionally, it registers itself with a Service Catalog at startup and deregisters upon shutdown.

## Features
- **Dynamic Configuration**: The MQTT broker details and machine types are fetched dynamically from the service catalog.
- **MQTT Integration**: The service listens for machine availability updates via MQTT and publishes aggregated data.
- **Real-time Monitoring**: Updates machine availability status dynamically based on incoming MQTT messages.
- **Service Registration**: Automatically registers and deregisters itself with a service catalog at startup and shutdown.
- **Machine Data Aggregation**: Tracks the total number of available, occupied, and total machines for each machine type.
- **Graceful Shutdown**: Stops the service and MQTT client loop cleanly when interrupted.

## Installation

### Prerequisites
- Python 3.x
- Required libraries:
  - `paho-mqtt`
  - `requests`

## Usage

### Service Registration
The service registers itself with a service catalog at startup using the `register_service` function from `registration_functions.py`.

### Dynamic Configuration from the Service Catalog
Upon startup, the service retrieves the following information from the Service Catalog via a GET request:
  - **MQTT Broker and Port**: The service dynamically fetches the broker IP and port.
  - **Machine Types**: The list and count of machines (e.g., treadmills, elliptical trainers) are fetched and tracked.

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
The service does not require manual configuration of the MQTT broker or machine types. These details are fetched dynamically from the Service Catalog. The only required configuration is the Service Catalog's URL and the list of topic to which is needed subscription, which should be specified in the config.json file.

## Shutdown and Cleanup
To stop the service gracefully:
1. Press Ctrl+C in the terminal where the service is running.
2. The service will:
  - Deregister itself from the service catalog using the delete_service function from registration_functions.py.
  - Stop the MQTT client loop cleanly.