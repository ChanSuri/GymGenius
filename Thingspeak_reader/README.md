# Thingspeak Reader & ThingSpeak Integration

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Historical Data Handling](#Historical-Data-Handling) 
- [Service Registration](#service-registration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

---

## Overview
The **Thingspeak Reader** is a microservice responsible for retrieving historical data from the ThingSpeak IoT analytics platform. It collects environmental data, occupancy status, and machine availability from multiple ThingSpeak channels and generates CSV files for historical analysis.

This service periodically fetches data from ThingSpeak and stores it locally, enabling easy retrieval via HTTP GET requests.

---

## Features
- **Automatic Data Retrieval**: Fetches data from predefined ThingSpeak channels at regular intervals.
- **Historical Data Storage**: Saves retrieved data into CSV files for future analysis.
- **HTTP Endpoint for Data Access**: Provides an HTTP GET interface to download historical data.
- **Service Registration and Deregistration**: Registers itself in a service catalog and unregisters on shutdown.
- **Multi-Channel Support**: Reads data from multiple predefined channels based on configuration.
  
---

## Installation

### Prerequisites
- **Python 3.x**
- **requests**
- **pandas**
- **cherrypy**
- **json**
- **threading**
- **signal**
- **os**
- **time**

---
## Configuration

The service requires two configuration files:

- `config_thingspeak.json`: Defines the ThingSpeak API endpoints and channels to retrieve data from.
- `config_thingspeak_reader.json`: Defines the service registration details and endpoint information.


---
## Usage

### Data Collection

The **Thingspeak Reader** fetches data periodically from ThingSpeak and saves it in CSV format. It reads:
- **Temperature and Humidity**
- **Current Occupancy**
- **Machine Availability** (for cardio and lifting room)

## HTTP GET Requests for Historical Data

To retrieve historical data for a specific channel, send a GET request:

`"http://thingspeak_reader:8089/thingspeak_adaptor?channel=entrance"`

This will return the CSV file containing historical records.

Available channels (defined in `config_thingspeak.json`):

- **Entrance**
- **Changing Room**
- **Cardio Room**
- **Lifting Room**

---

## Historical Data Handling

The Thingspeak Reader saves data as CSV files, where each room has a separate CSV file (`thingspeak_data_<channel_name>.csv`).

---

## Service Registration

On startup, the service registers itself with the service catalog to ensure discoverability.

**Registration Process**

1. The service sends a registration request to the catalog.

2. If already registered, it updates the registration timestamp.

3. On shutdown, it deregisters itself.

At startup, the Thingspeak Reader registers itself with the service catalog using the `register_service` function. This allows external systems to query the service's status and details.

- **Service ID**: `thingspeak_reader`
- **Description**: "Generates historical records on occupancy, usage, and conditions for each room"
- **Endpoint**: The service registers an endpoint that can be used for monitoring or management, such as `http://thingspeak_reader:8089/thingspeak_reader`.

---

## Shutdown and Cleanup

To stop the service gracefully, press `Ctrl+C`. This triggers the signal handler to:
- Deregister the service using the `delete_service()` function.
- Stop the MQTT client and cleanly shut down all processes.

The service ensures that the MQTT client disconnects properly and that the ThingSpeak data stream is closed without any interruptions.
