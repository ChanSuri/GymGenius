# Thingspeak Adaptor & ThingSpeak Integration

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [ThingSpeak Configuration](#thingspeak-configuration)
- [Service Registration](#service-registration)
- [Historical Data Handling](#historical-data-handling)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

---

## Overview
The **Thingspeak Adaptor** is a microservice designed to collect real-time environmental data, occupancy status, and machine availability in a gym environment. It listens to MQTT topics for aggregated machine availability, occupancy data, and room conditions (temperature and humidity). The service uploads the data to the **ThingSpeak** IoT analytics platform for storage and visualization using REST API calls.

Additionally, **TA_reader** generates historical data files based on the data from each specific room. It processes real-time data and saves historical information for future analysis, helping to track the availability of machines, occupancy, and environmental conditions like temperature and humidity in individual rooms.

---

## Features
- **MQTT Integration**: Subscribes to MQTT topics for aggregated machine availability, temperature, humidity, and occupancy.
- **ThingSpeak Data Upload (via REST)**: Automatically uploads real-time data to configured ThingSpeak channels using RESTful HTTP requests.
- **Rate-Limited Updates**: Ensures that data is uploaded no more than once every 30 seconds to avoid overloading ThingSpeak.
- **Service Registration and Deregistration**: Registers the service with a service catalog on startup and deregisters it on shutdown.
- **Historical Data Generation (Room-Specific)**: The system saves historical information for each room (Entrance Room, Cardio Room, Lifting Room and Changing Room) using **TA_reader**, generating separate files for tracking data from individual rooms.

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
- **Temperature and Humidity** for the *Cardio Room*, *Lifting Room*, and *Changing Room*.
- **Occupancy Status** for the entire gym in the *Entrance Room*.
- **Aggregated Machine Availability** for various gym machines (e.g., treadmills, elliptical trainers).

Once data is collected, it is uploaded to ThingSpeak via REST API calls, where it can be visualized and analyzed.

In addition, **TA_reader** processes this real-time data and generates files that store historical information for each room separately. These historical records provide insights into the occupancy, availability, usage, and environmental conditions in the *Cardio Room*, *Lifting Room*, *Changing Room*, and *Entrance Room*.

---

## MQTT Topics

### Subscribed Topics
- **Temperature & Humidity**:
  - `gym/environment/cardio_room`, `gym/environment/lifting_room`, and `gym/environment/changing_room` for monitoring room conditions.
- **Current Occupancy**:
  - `gym/occupancy/current` for tracking the current number of clients in the gym.
- **Aggregated Machine Availability**:
  - `gym/group_availability/{machine_type}` for receiving real-time aggregated machine availability data. The system listens to multiple machine types, such as:
    - `gym/group_availability/treadmill`
    - `gym/group_availability/elliptical_trainer`
    - `gym/group_availability/stationary_bike`

### Published Topics
- The **Thingspeak Adaptor** does not publish data back to MQTT. Its purpose is to forward the data from MQTT to **ThingSpeak** via REST API calls.

---

## ThingSpeak Configuration

The service is configured to upload data to specific **ThingSpeak** channels for different rooms and aspects of the gym. Data is sent to ThingSpeak via REST API using write API keys for each room. Below is the configuration for each room and the corresponding data types:

### *Cardio Room*
- **Temperature**: Field 1 in ThingSpeak.
- **Humidity**: Field 2 in ThingSpeak.
- **Machine Availability**:
  - **Treadmill**: Field 3.
  - **Elliptical Trainer**: Field 4.
  - **Stationary Bike**: Field 5.
  - **Rowing Machine**: Field 6.

This setup allows monitoring the environmental conditions in the *Cardio Room* as well as the availability of cardio machines.

### *Lifting Room*
- **Temperature**: Field 1 in ThingSpeak.
- **Humidity**: Field 2 in ThingSpeak.
- **Machine Availability**:
  - **Cable Machine**: Field 3.
  - **Leg Press Machine**: Field 4.
  - **Smith Machine**: Field 5.
  - **Lat Pulldown Machine**: Field 6.

This setup provides insights into the availability of lifting machines as well as environmental factors in the *Lifting Room*.

### *Changing Room*
- **Temperature**: Field 1 in ThingSpeak.
- **Humidity**: Field 2 in ThingSpeak.

The *Changing Room* is monitored for temperature and humidity, helping maintain comfort levels and proper ventilation.

### *Entrance*
- **Current Occupancy**: Field 1 in ThingSpeak.

This allows the gym to track how many clients are currently present in the gym through the *Entrance* data.

Each **ThingSpeak** channel must have a unique **write API key** and corresponding fields, which are defined in the `settings.json` file.

---

## Service Registration

At startup, the Thingspeak Adaptor registers itself with the service catalog using the `register_service` function. This allows external systems to query the service's status and details.

- **Service ID**: `thingspeak_adaptor`
- **Description**: "Manages data uploads to ThingSpeak"
- **Endpoint**: The service registers an endpoint that can be used for monitoring or management, such as `http://localhost:8080/thingspeak_adaptor`.

---

## Historical Data Handling

**TA_reader** processes the real-time data collected by the Thingspeak Adaptor and generates historical data files for each individual room. This allows the gym to maintain detailed historical records, which can be used for analysis, reporting, or predictive maintenance.

- **Room-Specific Data Files**: Historical data is saved separately for each room, ensuring that machine availability, occupancy, and environmental conditions (temperature, humidity) are tracked at a granular level.
- **File Structure**: Separate files are generated for rooms such as the *Entrance Room*, *Cardio Room*, *Lifting Room*, and *Changing Room*, allowing detailed analysis of machine usage, environmental conditions, and occupancy trends over time.

This room-specific data can be used to analyze gym usage patterns, machine availability, or environmental factors, helping to optimize operations and improve the gym experience.

---

## Shutdown and Cleanup

To stop the service gracefully, press `Ctrl+C`. This triggers the signal handler to:
- Deregister the service using the `delete_service()` function.
- Stop the MQTT client and cleanly shut down all processes.

The service ensures that the MQTT client disconnects properly and that the ThingSpeak data stream is closed without any interruptions.

---

This README provides an overview of the **Thingspeak Adaptor** service and its integration with **ThingSpeak**. The service efficiently bridges the gap between MQTT-based real-time data and the visualization capabilities of ThingSpeak, using REST API calls. It also provides a system for generating and storing room-specific historical data through **TA_reader**.



