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
- **Service Registration**: Add a new service to the catalog.
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
You can interact with the service's REST API at `http://localhost:8080/` to perform GET, POST, and DELETE operations on the service catalog.

## REST API

# Service Catalog API Documentation

## Get All Services or a Specific Service
- **Endpoint**: `/` or `/<service_id>`
- **Method**: GET
- **Description**: 
  - Retrieves a list of all registered services in the service registry if no `service_id` is provided.
  - Retrieves details about a specific service by `service_id` if provided.
  
- **Response for All Services**:
    ```json
    {
      "status": "success",
      "services": [
          {
              "service_id": "example_service1",
              ...
          },
          ...
      ]
    }
    ```
  
- **Response for a Specific Service**:
    ```json
    {
      "status": "success",
      "service": {
          "service_id": "example_service1",
          ...
      }
    }
    ```

### Register a New Service
- **Endpoint**: `/`
- **Method**: POST
- **Request Body**:
  \```json
  {
    "service_id": "new_service",
    ...
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

