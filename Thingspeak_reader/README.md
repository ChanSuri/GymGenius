# Thingspeak Reader & ThingSpeak Integration

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
- [Usage](#usage)
- [ThingSpeak Configuration](#thingspeak-configuration)
- [Service Registration](#service-registration)
- [Historical Data Handling](#historical-data-handling)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

---

## Overview
The **Thingspeak Reader** is a microservice dedicated to **retrieving data** from ThingSpeak channels and **storing** it in local CSV files. It also provides an HTTP **GET** endpoint (using CherryPy) to **serve** these CSV files on demand. By periodically fetching data from ThingSpeak, this service helps maintain a **historical** record of gym-related information, such as occupancy, machine availability, and environmental data, for each specific room.

---

## Features
- **Periodic ThingSpeak Retrieval**: Polls ThingSpeak channels at configurable intervals to download up to 5000 recent entries.
- **CSV File Generation**: Organizes and saves the data from each channel into separate CSV files for easy offline analysis.
- **HTTP Endpoint**: Serves the CSV files through a GET request; clients can specify which channel’s data they want.
- **Dynamic Configuration**: Retrieves the necessary service information (channels, endpoints, update intervals) from a service catalog at startup.
- **Service Registration and Deregistration**: Registers the service with a service catalog on startup and deregisters it on shutdown.
  
---

## Installation

### Prerequisites
- **Python 3.x**
- **requests** library (to perform HTTP GET calls to ThingSpeak)
- **pandas** library (to parse and manage CSV data)
- **cherrypy** library (for the HTTP server functionality)

---

## Usage

### Service Registration
At startup, the service registers itself with the service catalog using the `register_service` function from `registration_functions.py`.

---

### Periodic Updates
- TA_reader fetches new data from each configured **ThingSpeak channel** at a predefined **update interval** (e.g., 30 seconds).  
- Retrieved data is stored in CSV files, **overwriting** previous data with the latest snapshot from ThingSpeak.  
- Files are named as follows:  
thingspeak_data_<channel_name>.csv
For example, data for the **Entrance Room** would be stored as: thingspeak_data_entrance.csv

---

### Retrieve Historical Data
- To access a specific room’s historical data, make an HTTP **GET request** to the TA_reader endpoint, specifying the `channel` query parameter.  
- Example request using:
```http://localhost:8089/?channel=entrance"```
**Response**: The service returns the CSV file content for the requested channel (e.g., entrance).
If the channel does not exist or the CSV file is unavailable, the service returns a 404 Not Found error.

