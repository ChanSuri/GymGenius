# Resource Catalog Management

## Table of Contents
•⁠  ⁠[Overview](#overview)
•⁠  ⁠[Features](#features)
•⁠  ⁠[Installation](#installation)
•⁠  ⁠[Usage](#usage)
•⁠  ⁠[REST API](#rest-api)
•⁠  ⁠[Service Configuration](#service-configuration)
•⁠  ⁠[Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Resource Catalog Management** system is a microservice designed to manage a registry of devices. It allows for the creation, retrieval, updating, and deletion of device entries through a RESTful API. The devices are stored in a local JSON file (⁠ device_registry.json ⁠) to ensure data persistence.

## Features
•⁠  ⁠**Device Registration**: Allows new devices to be registered in the catalog.
•⁠  ⁠**Device Retrieval**: Fetch details of a specific device or all devices.
•⁠  ⁠**Device Update**: Update details of an existing device in the catalog.
•⁠  ⁠**Device Deletion**: Remove a device from the catalog.
•⁠  ⁠**Data Persistence**: Stores the device registry in a JSON file for persistence.

## Installation

### Prerequisites
•⁠  ⁠Python 3.x
•⁠  ⁠⁠ cherrypy ⁠ library
•⁠  ⁠⁠ json ⁠ library (part of Python standard library)
•⁠  ⁠⁠ os ⁠ library (part of Python standard library)

## Usage

### Interacting with the REST API
You can interact with the service's REST API at ⁠ http://localhost:8081/ ⁠ to perform CRUD operations on the device catalog.

## REST API

### Get All Devices
•⁠  ⁠**Endpoint**: ⁠ / ⁠
•⁠  ⁠**Method**: GET
•⁠  ⁠**Response**:
  \⁠  json
  {
    "status": "success",
    "devices": [
        {
            "device_id": "example_device",
            "description": "Example device description",
            "status": "active",
            "location": "example_room"
        },
        ...
    ]
  }
  \ ⁠

### Get a Specific Device
•⁠  ⁠**Endpoint**: ⁠ /<device_id> ⁠
•⁠  ⁠**Method**: GET
•⁠  ⁠**Response**:
  \⁠  json
  {
    "status": "success",
    "device": {
        "device_id": "example_device",
        "description": "Example device description",
        "status": "active",
        "location": "example_room"
    }
  }
  \ ⁠

### Register a New Device
•⁠  ⁠**Endpoint**: ⁠ / ⁠
•⁠  ⁠**Method**: POST
•⁠  ⁠**Request Body**:
  \⁠  json
  {
    "device_id": "new_device",
    "description": "New device description",
    "status": "active",
    "location": "example_room"
  }
  \ ⁠
•⁠  ⁠**Response**:
  \⁠  json
  {
    "status": "success",
    "message": "Device registered successfully"
  }
  \ ⁠

### Update an Existing Device
•⁠  ⁠**Endpoint**: ⁠ /<device_id> ⁠
•⁠  ⁠**Method**: PUT
•⁠  ⁠**Request Body**:
  \⁠  json
  {
    "description": "Updated device description",
    "status": "inactive"
  }
  \ ⁠
•⁠  ⁠**Response**:
  \⁠  json
  {
    "status": "success",
    "message": "Device updated successfully"
  }
  \ ⁠

### Delete a Device
•⁠  ⁠**Endpoint**: ⁠ /<device_id> ⁠
•⁠  ⁠**Method**: DELETE
•⁠  ⁠**Response**:
  \⁠  json
  {
    "status": "success",
    "message": "Device deleted successfully"
  }
  \ ⁠

## Service Configuration
The service configuration includes the port and host settings for the CherryPy server, as well as session management and MethodDispatcher configuration.

•⁠  ⁠**Server Port**: ⁠ 8081 ⁠
•⁠  ⁠**Host**: ⁠ 0.0.0.0 ⁠ (to listen on all network interfaces)

## Shutdown and Cleanup
When the service is stopped CherryPy will ensure that all processes are terminated cleanly.