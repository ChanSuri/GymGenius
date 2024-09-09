# Service Catalog Management

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [REST API](#rest-api)
- [Service Configuration](#service-configuration)
- [Shutdown and Cleanup](#shutdown-and-cleanup)

## Overview
The **Service Catalog Management** system is a microservice designed to manage a registry of services. It allows for the creation, retrieval, updating, and deletion of service entries through a RESTful API. The services are stored in a local JSON file (`service_registry.json`) to persist the data.

## Features
- **Service Registration**: Allows new services to be registered in the catalog.
- **Service Retrieval**: Fetch details of a specific service or all services.
- **Service Update**: Update details of an existing service in the catalog.
- **Service Deletion**: Remove a service from the catalog.
- **Data Persistence**: Stores the service registry in a JSON file for persistence.

## Installation

### Prerequisites
- Python 3.x
- `cherrypy` library
- `json` library (part of Python standard library)
- `os` library (part of Python standard library)

## Usage

### Interacting with the REST API
You can interact with the service's REST API at `http://localhost:8080/` to perform GET, POST and DELETE operations on the service catalog.

## REST API

### Get All Services
- **Endpoint**: `/`
- **Method**: GET
- **Response**:
  \```json
  {
    "status": "success",
    "services": [
        {
            "service_id": "example_service",
            "description": "Example service description",
            "status": "active",
            "endpoint": "http://localhost:8081/example"
            "last_update": "YYYY-MM-DD HH:MM:SS"
        },
        ...
    ]
  }
  \```

### Get a Specific Service
- **Endpoint**: `/<service_id>`
- **Method**: GET
- **Response**:
  \```json
  {
    "status": "success",
    "service": {
        "service_id": "example_service",
        "description": "Example service description",
        "status": "active",
        "endpoint": "http://localhost:8081/example"
        "last_update": "YYYY-MM-DD HH:MM:SS"
    }
  }
  \```

### Register a New Service
- **Endpoint**: `/`
- **Method**: POST
- **Request Body**:
  \```json
  {
    "service_id": "new_service",
    "description": "New service description",
    "status": "active",
    "endpoint": "http://localhost:8082/new_service"
    "last_update": "YYYY-MM-DD HH:MM:SS"
  }
  \```
- **Response**:
  \```json
  {
    "status": "success",
    "message": "Service registered successfully"
  }
  \```

### Delete a Service
- **Endpoint**: `/<service_id>`
- **Method**: DELETE
- **Response**:
  \```json
  {
    "status": "success",
    "message": "Service deleted successfully"
  }
  \```

## Service Configuration
The service configuration includes the port and host settings for the CherryPy server, as well as session management and MethodDispatcher configuration.

- **Server Port**: `8080`
- **Host**: `0.0.0.0` (to listen on all network interfaces)

## Shutdown and Cleanup
When the service is stopped CherryPy will ensure that all processes are terminated cleanly.

