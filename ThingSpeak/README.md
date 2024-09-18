# ThingSpeak
Thingspeak is a third-party software (https://thingspeak.com/) that provides REST Web Services. It is an open-data platform for the Internet of Things to store, post-process, and visualize data (through plots). REST APIs are also used to send historical data to the Occupancy monitoring and access control block and the telegram bot.

# Thingspeak Adapter
The Thingspeak Adaptor is an MQTT subscriber that receives measurements on environmental data and uploads them on Thingspeak through REST Web Services. Moreover, REST APIs are also used to send and receive data to/from Gym Catal

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
The **Thingspeak Adaptor** is a microservice designed to collect real-time environmental data, occupancy status, and machine availability in a gym environment. It listens to MQTT topics for aggregated machine availability, occupancy data, and room conditions (temperature and humidity). The service uploads the data to the **ThingSpeak** IoT analytics platform for storage and visualization.

The service supports real-time monitoring of gym conditions and ensures that data is regularly pushed to ThingSpeak channels for analysis and visualization.

---

## Features
- **MQTT Integration**: Subscribes to MQTT topics for aggregated machine availability, temperature, humidity, and occupancy.
- **ThingSpeak Data Upload**: Automatically uploads real-time data to configured ThingSpeak channels.
- **Rate-Limited Updates**: Ensures that data is uploaded no more than once every 30 seconds to avoid overloading ThingSpeak.
- **Service Registration and Deregistration**: Registers the service with a service catalog on startup and deregisters it on shutdown.

---

## Installation

### Prerequisites
- Python 3.x
- `paho-mqtt` library
- `requests` library (for HTTP communication with ThingSpeak)

---

## Usage

### Data Collection
The service collects data from MQTT topics and processes them in real time. Supported data types include:
- **Temperature and Humidity** for the *Cardio Room* and *Lifting Room*.
- **Occupancy Status** for the entire gym.
- **Aggregated Machine Availability** for various gym machines (e.g., treadmills, elliptical trainers).

Once data is collected, it is uploaded to ThingSpeak, where it can be visualized and analyzed.

---

## MQTT Topics

### Subscribed Topics
- **Temperature & Humidity**:
  - `gym/environment/cardio_room` and `gym/environment/lifting_room` for monitoring room conditions.
- **Current Occupancy**:
  - `gym/occupancy/current` for tracking the current number of clients in the gym.
- **Aggregated Machine Availability**:
  - `gym/group_availability/{machine_type}` for receiving real-time aggregated machine availability data. The system listens to multiple machine types, such as:
    - `gym/group_availability/treadmill`
    - `gym/group_availability/elliptical_trainer`
    - `gym/group_availability/stationary_bike`
  
### Published Topics
- The **Thingspeak Adaptor** does not publish data back to MQTT. Its purpose is to forward the data from MQTT to **ThingSpeak**.

---

## ThingSpeak Configuration

The service is configured to upload data to specific **ThingSpeak** channels, each corresponding to a different room or aspect of the gym. 

For example:
- *Cardio Room*: Temperature, humidity, treadmill availability, etc.
- *Lifting Room*: Temperature, humidity, and availability of machines like the cable machine and leg press machine.
- *Entrance*: Tracks the current occupancy of the gym.

Each **ThingSpeak** channel must have a unique **write API key** and corresponding fields, which are defined in the `settings.json` file.

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

---

This README provides an overview of the **Thingspeak Adaptor** service and its integration with **ThingSpeak**. The service efficiently bridges the gap between MQTT-based real-time data and the visualization capabilities of ThingSpeak, making it an ideal solution for gym monitoring and IoT-based data analytics.
