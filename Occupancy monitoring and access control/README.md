# Occupancy Monitoring and Prediction Service

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)


## Overview
The **Occupancy Monitoring and Prediction Service** is a microservice designed to monitor and predict the occupancy of a gym. It uses MQTT to track entry and exit events, maintains historical data, and employs a linear regression model to predict future occupancy levels based on time slots and days of the week. The service also publishes the current occupancy and predictions to specific MQTT topics.

## Features
- **MQTT Integration**: Subscribes to entry and exit events and updates the current occupancy accordingly.
- **Occupancy Tracking**: Maintains historical data on occupancy by time slot and day of the week.
- **Prediction Model**: Uses a linear regression model to predict future occupancy levels.
- **Data Publishing**: Publishes current occupancy and predicted occupancy to MQTT topics.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `numpy` library
- `scikit-learn` library

## Usage

### Service Registration
The service registers itself at startup by calling the `register_service` function.

The service will connect to the MQTT broker and begin listening for entry and exit events. It will update the current occupancy, record historical data, and publish predictions.

## MQTT Topics

### Subscribed Topics
- **Occupancy Entry (`gym/occupancy/entry`)**: Increments the current occupancy when a person enters the gym.
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
  
- **Occupancy Exit (`gym/occupancy/exit`)**: Decrements the current occupancy when a person exits the gym.
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

### Published Topics
- **Current Occupancy (`gym/occupancy/current`)**: Publishes the current number of people present in the gym. 
  Example payload:
  \```json
  {
    "topic": "gym/occupancy/current",
    "message": {
      "device_id": "Occupancy_block",
      "timestamp": "YYYY-MM-DD HH:MM:SS",
      "data": {
        "current_occupancy": value,
        "unit": "count"
      }
    }
  }
  \```

- **Prediction Matrix (`gym/occupancy/prediction`)**: Publishes the predicted occupancy for different time slots and days of the week.
  Example payload:
  \```json
  {
    "topic": "gym/occupancy/prediction",
    "message": {
      "device_id": "Occupancy_block",
      "timestamp": "YYYY-MM-DD HH:MM:SS",
      "data": {
        "prediction_matrix": [[5, 6, ...], [...], ...]
      }
    }
  }
  \```

## Service Configuration
The service can be configured to monitor and predict gym occupancy based on different time slots and days of the week. In the current setup, the service divides each day into 9 time slots (from 08:00 to 24:00) and tracks occupancy across 7 days of the week.

Example time slot configuration:
- Time Slot 0: 08:00 - 10:00
- Time Slot 1: 10:00 - 12:00
- Time Slot 2: 12:00 - 14:00
- ...

The service uses these slots to record historical data and generate predictions.

## Shutdown and Cleanup
To stop the service gracefully, press `Ctrl+C`. The signal handler will:
- Stop the MQTT client loop cleanly.
- Ensure that the service is deregistered from the service catalog.
