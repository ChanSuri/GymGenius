# Occupancy Monitoring and Prediction Service

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
The **Occupancy Monitoring and Prediction Service** is a microservice designed to monitor and predict the occupancy of a gym. It uses MQTT to track entry and exit events and employs a linear regression model to predict future occupancy levels based on time slots and days of the week. The service also provides a RESTful API to let the clients retrieve the current occupancy and the predicted occupancy matrix.

## Features
- **MQTT Integration**: Subscribes to entry and exit events and updates the current occupancy accordingly.
- **Occupancy Tracking**: Maintains data on occupancy by time slot and day of the week.
- **Prediction Model**: Trains a linear regression model to predict future occupancy based on historical data.
- **REST API**: Provides an endpoint to check the current occupancy and view the predicted occupancy matrix.

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `cherrypy` library
- `numpy` library
- `scikit-learn` library
- `requests` library


## Usage

### Service Registration
The service registers itself at startup by calling the `register_service` function. Ensure that this function is correctly defined in `registration_functions.py`.

### Interacting with the REST API
You can interact with the service's REST API at `http://localhost:8083/occupancy` to retrieve the current occupancy and the prediction matrix.

## MQTT Topics

### Occupancy Entry (`gym/occupancy/entry`)
- This topic is used to track when a person enters the gym. Each message increments the occupancy count.
- Example payload:
  \```json
  {
    "event": "entry"
  }
  \```

### Occupancy Exit (`gym/occupancy/exit`)
- This topic is used to track when a person exits the gym. Each message decrements the occupancy count.
- Example payload:
  \```json
  {
    "event": "exit"
  }
  \```

## REST API
The service provides a REST API to retrieve the current occupancy and the prediction matrix.

- **Endpoint**: `/occupancy`
- **Method**: GET
- **Response**:
  \```json
  {
    "status": "success",
    "time": "YYYY-MM-DD HH:MM:SS",
    "current_occupancy": 42,
    "prediction_matrix": [[0.5, 0.6, ...], [...], ...]
  }
  \```

## Service Configuration
The service configuration includes MQTT broker details, thresholds for training the model, and the time slots used for tracking occupancy.

- **MQTT Broker**: `test.mosquitto.org` on port `1883`.
- **Time Slots**: 9 slots of 2 hours covering the hours from 8:00 to 24:00.
- **Minimum Training Samples**: At least 2 data points per time slot/day combination.

## Shutdown and Cleanup
When the service is stopped, the signal handler will ensure that the MQTT client disconnects cleanly and the service is properly stopped.

