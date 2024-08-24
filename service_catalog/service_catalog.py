import cherrypy
import json
import os

# Path to the service_registry.json file
REGISTRY_FILE = 'service_registry.json'

def load_registry():
    """Loads the service registry from the file."""
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_registry(registry):
    """Saves the service registry to the file."""
    with open(REGISTRY_FILE, 'w') as file:
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
            if service:
                return json.dumps({"status": "success", "service": service})
            else:
                raise cherrypy.HTTPError(404, "Service not found")
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
        
        # Check if the service already exists
        if service_id in service_registry:
            raise cherrypy.HTTPError(409, "Service already exists")
        
        # Add the service to the registry and save it to the file
        service_registry[service_id] = input_data
        save_registry(service_registry)
        return json.dumps({"status": "success", "message": "Service registered successfully"})

    def PUT(self, *uri, **params):
        # Ensure service_id is provided in the URI
        if len(uri) == 0:
            raise cherrypy.HTTPError(400, "service_id is required")

        service_id = uri[0]
        
        # Check if the service exists
        if service_id not in service_registry:
            raise cherrypy.HTTPError(404, "Service not found")

        # Read and decode the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)
        
        # Update the service in the registry
        service_registry[service_id].update(input_data)
        save_registry(service_registry)
        return json.dumps({"status": "success", "message": "Service updated successfully"})

    def DELETE(self, *uri, **params):
        # Ensure service_id is provided in the URI
        if len(uri) == 0:
            raise cherrypy.HTTPError(400, "service_id is required")

        service_id = uri[0]
        
        # Check if the service exists in the registry
        if service_id in service_registry:
            # Remove the service from the registry
            del service_registry[service_id]
            save_registry(service_registry)
            return json.dumps({"status": "success", "message": "Service deleted successfully"})
        else:
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
