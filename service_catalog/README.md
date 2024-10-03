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

# Service Catalog API Documentation

## Get All Services
- **Endpoint**: `/`
- **Method**: GET
- **Description**: Retrieves a list of all registered services in the service registry.
- **Response**:
    ```json
    {
      "status": "success",
      "services": [
          {
              "service_id": "example_service",
              "description": "Example service description",
              "status": "active",
              "endpoints": {
                  "task1": "http://localhost:8081/example/task1",
                  "task2": "http://localhost:8081/example/task2"
              },
              "mqtt_published_topics": {
                  "task1": "gym/occupancy/example1",
                  "task2": "gym/occupancy/example2"
              },
              "last_update": "YYYY-MM-DD HH:MM:SS"
          },
          ...
      ]
    }
    ```

## Get a Specific Service
- **Endpoint**: `/<service_id>`
- **Method**: GET
- **Description**: Retrieves details about a specific service by `service_id`.
- **Response**:
    ```json
    {
      "status": "success",
      "service": {
          "service_id": "example_service",
          "description": "Example service description",
          "status": "active",
          "endpoints": {
              "task1": "http://localhost:8081/example/task1",
              "task2": "http://localhost:8081/example/task2"
          },
          "mqtt_published_topics": {
              "task1": "gym/occupancy/example1",
              "task2": "gym/occupancy/example2"
          },
          "last_update": "YYYY-MM-DD HH:MM:SS"
      }
    }
    ```

## Get All Endpoints of a Specific Service
- **Endpoint**: `/<service_id>/endpoints`
- **Method**: GET
- **Description**: Retrieves a list of all endpoints for the specified service.
- **Response**:
    ```json
    {
      "status": "success",
      "endpoints": {
          "task1": "http://localhost:8081/example/task1",
          "task2": "http://localhost:8081/example/task2"
      }
    }
    ```

## Get All MQTT Topics of a Specific Service
- **Endpoint**: `/<service_id>/mqtt_topics`
- **Method**: GET
- **Description**: Retrieves a list of all MQTT published topics for the specified service.
- **Response**:
    ```json
    {
      "status": "success",
      "mqtt_published_topics": {
          "task1": "gym/occupancy/example1",
          "task2": "gym/occupancy/example2"
      }
    }
    ```

## Get Specific Task Endpoint of a Service
- **Endpoint**: `/<service_id>/tasks/<task_id>`
- **Method**: GET
- **Description**: Retrieves the endpoint of a specific task within a service by `task_id`.
- **Response**:
    ```json
    {
      "status": "success",
      "task_endpoint": {
          "task_id": "task1",
          "endpoint": "http://localhost:8081/example/task1"
      }
    }
    ```

## Get Specific Task MQTT Topic of a Service
- **Endpoint**: `/<service_id>/tasks/<task_id>/mqtt_topic`
- **Method**: GET
- **Description**: Retrieves the MQTT published topic for a specific task within a service by `task_id`.
- **Response**:
    ```json
    {
      "status": "success",
      "mqtt_topic": {
          "task_id": "task1",
          "mqtt_topic": "gym/occupancy/example1"
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

