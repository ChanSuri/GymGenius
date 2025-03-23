
# Device Connector - Cardio Room 

## 📖 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [MQTT Topics](#mqtt-topics)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Device Connector for the Cardio Room** is a microservice designed to simulate sensors (DHT11, PIR, Button) and handle communication via MQTT. Its main responsibilities include:
- Registering devices in the **Resource Catalog**
- Publishing environmental data, machine availability, and occupancy events
- Managing HVAC control commands
- Simulating temperature with HVAC residual effects
- Removing inactive devices after 3 days

## ✅ Features
- **Sensor Simulation**: DHT11 (temperature/humidity), PIR (machine presence), Button
- **Device Registration**: Registers devices (e.g., sensors, HVAC systems) with the Resource Catalog.
- **MQTT Integration**: Subscribes to and publishes messages on various MQTT topics related to occupancy, environment, and machine availability.
- **Intelligent HVAC Control** with temperature and mode (cool/heat) management
- **SenML-compliant MQTT Publishing** on configurable topics
- **Inactive Device Management**
- **REST API** using **CherryPy**

## Installation
### Prerequisites
- Python 3.x
- Required libraries: `paho-mqtt`, `cherrypy`, `requests`

Install dependencies:
```bash
pip install paho-mqtt cherrypy requests
```

## Usage
### Starting the Service
```bash
python device_connector_cardio_room.py
```
The service will:
- Load configuration from `config_device_connector_cardio_room.json`
- Register itself with the **Service Catalog**
- Connect to the MQTT broker
- Subscribe to configured topics
- Start a thread to simulate sensors

### Available REST APIs
- `GET /environment`: Returns current temperature and humidity
- `GET /hvac_status`: Returns HVAC state and mode

Example:
```bash
curl http://localhost:8092/environment
```

## MQTT Topics
### Subscribed Topics
`gym/hvac/control/#`: Receives HVAC control commands     
`gym/hvac/on_off/#`: Receives administrative HVAC commands

**Example HVAC Payload:**
```json
{
  "topic": "gym/hvac/control/cardio_room",
  "message": {
    "device_id": "hvac_controller",
    "timestamp": "2025-03-21 10:00:00",
    "data": {
      "control_command": "turn_on",
      "mode": "cool"
    }
  }
}
```

### Published Topics
`gym/environment/<roomID>`: Publishes temperature and humidity readings
`gym/availability/<machineID>`: Publishes cardio machine availability

**Example Environment Payload (SenML):**
```json
{
  "bn": "gym/environment/cardio_room",
  "e": [
    {"n": "temperature", "u": "Cel", "t": 1711017600, "v": 22.5},
    {"n": "humidity", "u": "%", "t": 1711017600, "v": 45}
  ]
}
```

## Service Configuration
The service reads settings from `config_device_connector_cardio_room.json`. Key parameters:
- `service_catalog`: Service Catalog URL
- `resource_catalog`: Resource Catalog URL
- `subscribed_topics`, `published_topics`
- `simulation_parameters`: sensor simulation intervals
- `enable_dht11`, `enable_pir`, `enable_button`

Example:
```json
"simulation_parameters": {
  "dht11_seconds": 5,
  "pir_machine_type": "cardio",
  "pir_machines_per_type": 4,
  "pir_seconds": 2,
  "button_seconds": null
}
```

## Shutdown and Cleanup
- Graceful shutdown with `Ctrl+C`
- MQTT client loop stops cleanly

---
 **Important Notes**
- Simulated temperature considers HVAC effects over time
- Inactive devices (no updates for >3 days) are automatically removed from the Resource Catalog
- REST endpoints are provided for monitoring and testing

---
