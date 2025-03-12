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

-`config_thingspeak.json`: Defines the ThingSpeak API endpoints and channels to retrieve data from.
-

---
## Usage

### Service Registration
At startup, the service registers itself with the service catalog using the `register_service` function from `registration_functions.py`.


### Periodic Updates
- TA_reader fetches new data from each configured **ThingSpeak channel** at a predefined **update interval** (e.g., 30 seconds).  
- Retrieved data is stored in CSV files, **overwriting** previous data with the latest snapshot from ThingSpeak.  
- Files are named as follows:  ```thingspeak_data_<channel_name>.csv```

For example, data for the **Entrance Room** would be stored as:
```thingspeak_data_entrance.csv```

### Retrieve Historical Data
- To access a specific room’s historical data, make an HTTP **GET request** to the TA_reader endpoint, specifying the `channel` query parameter.  
- Example request using:
```http://localhost:8089/?channel=entrance"```
**Response**: The service returns the CSV file content for the requested channel (e.g., entrance).
If the channel does not exist or the CSV file is unavailable, the service returns a 404 Not Found error.

---

## Dynamic Configuration from the Service Catalog

At startup, **TA_reader** can optionally fetch configuration details by issuing a **GET request** to a **service catalog**. These details may include:

- **ThingSpeak Channels**: A list of channels (`IDs`, `read API keys`) to poll for each room or sensor group.
- **Update Interval**: How often (**in seconds**) TA_reader should request new data from **ThingSpeak**.
- **CSV Storage Paths** (if needed): Where to store the CSV files (by default, in the same directory).
- **Service Endpoint**: The HTTP endpoint for external clients to access the CSV files, e.g.:
`http://thingspeak_reader:8089`
- **Registration Settings**: Information for registering or updating the service’s entry in the catalog (e.g., `service ID`, `status`, and `description`).

After fetching this information, **TA_reader**:
1. **Starts polling** the specified channels at the indicated interval.
2. **Generates or updates** local CSV files.
3. **Serves** them via **HTTP GET requests** on the configured endpoint.

---

## ThingSpeak Configuration

TA_reader also relies on ThingSpeak-specific details, typically found in a local JSON file (e.g., config_thingspeak.json). For each channel:

-**channel_id**: The numerical ID representing a ThingSpeak channel.
-**read_api_key**: The API key enabling read-access to that channel.
-**fields**: A mapping of your preferred field names (e.g., temperature, humidity) to the actual ThingSpeak field numbers (field1, field2, etc.).

---

---

## Service Registration

At startup, the Thingspeak Reader registers itself with the service catalog using the `register_service` function. This allows external systems to query the service's status and details.

- **Service ID**: `thingspeak_reader`
- **Description**: "Generates historical records on occupancy, usage, and conditions for each room"
- **Endpoint**: The service registers an endpoint that can be used for monitoring or management, such as `http://thingspeak_reader:8080/thingspeak_reader`.

## Shutdown and Cleanup

To stop the service gracefully, press `Ctrl+C`. This triggers the signal handler to:
- Deregister the service using the `delete_service()` function.
- Stop the MQTT client and cleanly shut down all processes.

The service ensures that the MQTT client disconnects properly and that the ThingSpeak data stream is closed without any interruptions.



