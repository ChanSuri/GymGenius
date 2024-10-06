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
The **Occupancy Monitoring and Prediction Service** is a microservice designed to monitor and predict the occupancy of a gym. It subscribes to MQTT topics to track entry and exit events and uses a linear regression model to predict future occupancy levels based on time slots and days of the week. The service dynamically retrieves MQTT broker information, time slots, and ThingSpeak details from the service catalog at startup. The service also publishes the current occupancy and predictions to specific MQTT topics.

## Features
- **Dynamic Configuration**: The MQTT broker details, time slots, and ThingSpeak URL are fetched dynamically from the service catalog.
- **MQTT Integration**: Subscribes to entry and exit events and updates the current occupancy accordingly.
- **Occupancy Tracking**: Maintains historical data on occupancy by time slot and day of the week.
- **Prediction Model**: Uses a linear regression model to predict future occupancy levels.
- **Data Publishing**: Publishes current occupancy and predicted occupancy to MQTT topics.


## Installation

### Prerequisites
- Python 3.x
- Required libraries:
  - `paho-mqtt`
  - `numpy`
  - `pandas`
  - `scikit-learn`
  - `requests`

## Usage

### Service Registration
The service registers itself with a Service Catalog at startup using the `register_service` function from registration_functions.py.

### Dynamic Configuration from the Service Catalog
At startup, the service retrieves the following information from the service catalog via a GET request:
  - **MQTT Broker and Port**: The service fetches the MQTT broker IP and port from the service catalog.
  - **Time Slots**: The service dynamically retrieves the time slots configuration to track and predict gym occupancy.
  - **ThingSpeak URL**: The service retrieves the URL for fetching historical data.

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
The service configuration is dynamically fetched from the service catalog. The configuration includes:
  - **MQTT Broker Details**: The broker IP and port are retrieved via a GET request.
  - **Time Slots**: The service retrieves time slots configuration for occupancy prediction.
  - **ThingSpeak URL**: The service retrieves the ThingSpeak endpoint to fetch historical data for model training.

The only manual configuration required in the `config.json` file is:
  - **Service Catalog URL**: The URL of the service catalog from which the service retrieves the necessary information.
  - **MQTT Topics**: The topics to which the service subscribes and publishes.

## Shutdown and Cleanup
To stop the service gracefully, press `Ctrl+C`. The signal handler will:
- Deregister the service from the service catalog using the `delete_service` function from `registration_functions.py`.
- Stop the MQTT client loop and disconnect cleanly.
