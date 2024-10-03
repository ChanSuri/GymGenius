import cherrypy
import json
import os
from datetime import datetime

# Path to the service_registry.json file
SERVICE_REGISTRY_FILE = 'service_registry.json'

def load_registry():
    """Loads the service registry from the file."""
    if os.path.exists(SERVICE_REGISTRY_FILE):
        with open(SERVICE_REGISTRY_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_service_registry(registry):
    """Saves the service registry to the file."""
    with open(SERVICE_REGISTRY_FILE, 'w') as file:
        json.dump(registry, file, indent=4)

# Load the registry from the file at startup
service_registry = load_registry()

class ServiceCatalog:
    exposed = True

    def GET(self, *uri, **params):
        # If a service_id is provided in the URI, return the specific service
        if len(uri) > 0:
            service_id = uri[0]
            service = service_registry.get(service_id, None)
            if not service:
                raise cherrypy.HTTPError(404, "Service not found")
            
            # If additional parameters are provided, return specific information
            if len(uri) > 1:
                if uri[1] == "endpoints":
                    # Return all endpoints of the service
                    return json.dumps({"status": "success", "endpoints": service.get("endpoints", {})})
                elif uri[1] == "mqtt_topics":
                    # Return all MQTT topics of the service
                    return json.dumps({"status": "success", "mqtt_published_topics": service.get("mqtt_published_topics", {})})
                elif uri[1] == "tasks" and len(uri) > 2:
                    task_id = uri[2]
                    if len(uri) == 3:
                        # Return the specific task endpoint
                        task_endpoint = service.get("endpoints", {}).get(task_id, None)
                        if task_endpoint:
                            return json.dumps({"status": "success", "task_endpoint": {"task_id": task_id, "endpoint": task_endpoint}})
                        else:
                            raise cherrypy.HTTPError(404, "Task not found")
                    elif len(uri) == 4 and uri[3] == "mqtt_topic":
                        # Return the specific task MQTT topic
                        mqtt_topic = service.get("mqtt_published_topics", {}).get(task_id, None)
                        if mqtt_topic:
                            return json.dumps({"status": "success", "mqtt_topic": {"task_id": task_id, "mqtt_topic": mqtt_topic}})
                        else:
                            raise cherrypy.HTTPError(404, "MQTT topic for task not found")
                    else:
                        raise cherrypy.HTTPError(400, "Invalid request format")
                else:
                    raise cherrypy.HTTPError(400, "Invalid request format")
            else:
                # Return the specific service details
                return json.dumps({"status": "success", "service": service})
        else:
            # Return all services if no service_id is provided
            return json.dumps({"status": "success", "services": list(service_registry.values())})


    def POST(self, *uri, **params):
        # Read and decode the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)
        service_id = input_data.get("service_id")
        
        # Ensure service_id is present
        if not service_id:
            raise cherrypy.HTTPError(400, "service_id is required")
        
        # Build a dictionary for quick lookup
        services_by_id = {service["service_id"]: service for service in service_registry["services"]}

        # Check if the device already exists
        if service_id in services_by_id:
            existing_service = services_by_id[service_id]
            if input_data == existing_service:
                raise cherrypy.HTTPError(304, "Service already registered with the same data")

        # Add the device to the registry
        service_registry["services"].append(input_data)
        
        # update last update of the whole register 
        service_registry["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_service_registry(service_registry)
        return json.dumps({"status": "success", "message": "Service registered successfully"})

    def DELETE(self, *uri, **params):
        # Ensure service_id is provided in the URI
        if len(uri) == 0:
            raise cherrypy.HTTPError(400, "service_id is required")

        service_id = uri[0]

        # Check if the service exists in the registry
        for i, service in enumerate(service_registry["services"]):
            if service["service_id"] == service_id:
                # Remove the service from the registry
                del service_registry["services"][i]
                
                # Update lastUpdate
                service_registry["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_service_registry(service_registry)
                return json.dumps({"status": "success", "message": f"Service {service_id} deleted successfully"})
        
        # If no matching service was found
        raise cherrypy.HTTPError(404, "Service not found")


if __name__ == '__main__':
    # Configure the MethodDispatcher and session management
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }

    # Update CherryPy configuration with port and host settings
    cherrypy.config.update({'server.socket_port': 8080, 'server.socket_host': '0.0.0.0'})
    
    # Mount the ServiceCatalog class using MethodDispatcher
    cherrypy.tree.mount(ServiceCatalog(), '/', conf)
    
    # Start the CherryPy server
    cherrypy.engine.start()
    cherrypy.engine.block()
