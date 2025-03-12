# Thingspeak Adaptor & ThingSpeak Integration

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [ThingSpeak Configuration](#thingspeak-configuration)
- [Service Registration](#service-registration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

---

## Overview
The **Thingspeak Adaptor** is a microservice designed to collect real-time environmental data, occupancy status, and machine availability in a gym environment. It listens to MQTT topics for aggregated machine availability, occupancy data, and room conditions (temperature and humidity). The service uploads the data to the **ThingSpeak** IoT analytics platform for storage and visualization using REST API calls.

---

## Features
- **MQTT Integration**: Subscribes to MQTT topics for machine availability, temperature, humidity, and occupancy.
- **ThingSpeak Data Upload (via REST)**: Automatically uploads real-time data to configured ThingSpeak channels using RESTful HTTP requests.
- **Service Registration and Deregistration**: Registers the service with a service catalog on startup and deregisters it on shutdown.

---

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `requests` library (for HTTP communication with ThingSpeak)
- `cherrypy` library (for handling GET requests for historical data)

---

## Usage

### Data Collection
The service collects data from MQTT topics and processes them in real time. Supported data types include:
- **Temperature and Humidity** for the *Cardio Room*, *Lifting Room*, *Changing Room*, and *Entrance Room*.
- **Occupancy Status** for the entire gym in the *Entrance Room*.
- **Aggregated Machine Availability** for various gym machines (e.g., treadmills, elliptical trainers).

Once data is collected, it is uploaded to ThingSpeak via REST API calls, where it can be visualized and analyzed.

---

## MQTT Topics

### Subscribed Topics
- **Temperature & Humidity**:
  - The service subscribes to the following topics to monitor environmental conditions for each room, provided by the `device_connector` service:
    - `gym/environment/entrance`
    - `gym/environment/changing_room`
    - `gym/environment/lifting_room`
    - `gym/environment/cardio_room`
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
- **Current Occupancy**:
  - The service listens to `gym/occupancy/current`, a topic provided by the `occupancy` service, to track the current number of clients in the gym.

  - Example payload:
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
- **Aggregated Machine Availability**:
  - The service subscribes to `gym/group_availability/#` to receive real-time aggregated machine availability data, provided by the `machine_availability` service. This includes machines like treadmills, elliptical trainers, stationary bikes, and others.

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
### Published Topics
- The **Thingspeak Adaptor** does not publish data back to MQTT. Its purpose is to forward the data from MQTT to **ThingSpeak** via REST API calls.

---

## ThingSpeak Configuration

The service is configured to upload data to specific **ThingSpeak** channels for different rooms and aspects of the gym. Data is sent to ThingSpeak via REST API using write API keys for each room. Below is the configuration for each room and the corresponding data types:

### *Cardio Room*
- **Temperature**: Field 1 in ThingSpeak.
- **Humidity**: Field 2 in ThingSpeak.
- **Machine Availability**:
  - **Treadmill**: Field 3 in ThingSpeak.
  - **Elliptical Trainer**: Field 4 in ThingSpeak.
  - **Stationary Bike**: Field 5 in ThingSpeak.
  - **Rowing Machine**: Field 6 in ThingSpeak.

This setup allows monitoring the environmental conditions in the *Cardio Room* as well as the availability of cardio machines.

### *Lifting Room*
- **Temperature**: Field 1 in ThingSpeak.
- **Humidity**: Field 2 in ThingSpeak.
- **Machine Availability**:
  - **Cable Machine**: Field 3 in ThingSpeak.
  - **Leg Press Machine**: Field 4 in ThingSpeak.
  - **Smith Machine**: Field 5 in ThingSpeak.
  - **Lat Pulldown Machine**: Field 6 in ThingSpeak.

This setup provides insights into the availability of lifting machines as well as environmental factors in the *Lifting Room*.

### *Changing Room*
- **Temperature**: Field 1 in ThingSpeak.
- **Humidity**: Field 2 in ThingSpeak.

The *Changing Room* is monitored for temperature and humidity, helping maintain comfort levels and proper ventilation.

### *Entrance*
- **Current Occupancy**: Field 1 in ThingSpeak.
- **Temperature**: Field 2 in ThingSpeak.
- **Humidity**: Field 3 in ThingSpeak.

This allows the gym to track how many clients are currently present in the gym, along with the environmental conditions in the *Entrance Room*.

Each **ThingSpeak** channel must have a unique **write API key** and corresponding fields, which are defined in the `config_thingspeak.json` file.

---

## Service Registration

At startup, the Thingspeak Adaptor registers itself with the service catalog using the `register_service` function. This allows external systems to query the service's status and details.

- **Service ID**: `thingspeak_adaptor`
- **Description**: "Manages data uploads to ThingSpeak"
- **Endpoint**: The service registers an endpoint that can be used for monitoring or management, such as `http://localhost:8080/thingspeak_adaptor`.

---

## Shutdown and Cleanup

To stop the service gracefully, press `Ctrl+C`. This triggers the signal handler to:
- Deregister the service using the `delete_service()` function.
- Stop the MQTT client and cleanly shut down all processes.

The service ensures that the MQTT client disconnects properly and that the ThingSpeak data stream is closed without any interruptions.


