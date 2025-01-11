import cherrypy
import json
import os
from datetime import datetime

# Path to the service_registry.json file
# SERVICE_REGISTRY_FILE = 'C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\service_catalog\\service_registry.json'
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
#print(service_registry)

class ServiceCatalog:
    exposed = True

    def GET(self, *uri, **params):
        # Se viene fornito un service_id nell'URI, restituisci il servizio specifico
        if len(uri) > 0:
            service_id = uri[0]
            service = service_registry.get(service_id, None)
            if not service:
                raise cherrypy.HTTPError(404, "Service not found")
            # Restituisci i dettagli del servizio specifico
            return json.dumps({"status": "success", "service": service})
        else:
            # Restituisci l'intero catalogo se non viene fornito nessun service_id
            return json.dumps({"status": "success", "catalog": service_registry})



    def POST(self, *uri, **params):
        # Read and decode the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)
        service_id = input_data.get("service_id")

        # Ensure service_id is present
        if not service_id:
            raise cherrypy.HTTPError(400, "service_id is required")

        # Build a dictionary for quick lookup
        services_by_id = {service["service_id"]: service for service in service_registry.get("services", [])}

        # Check if the service already exists
        if service_id in services_by_id:
            existing_service = services_by_id[service_id]
            if input_data == existing_service:
                raise cherrypy.HTTPError(304, "Service already registered with the same data")
            else:
                raise cherrypy.HTTPError(409, "Service exists but data differs. Update required.")

        # Add the service to the registry
        service_registry["services"].append(input_data)

        # Update last update of the whole register
        service_registry["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_service_registry(service_registry)
        return json.dumps({"status": "success", "message": "Service registered successfully"})
    
    def PUT(self, *uri, **params):
        # Read and decode the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)
        service_id = input_data.get("service_id")

        # Ensure service_id is present
        if not service_id:
            raise cherrypy.HTTPError(400, "service_id is required")

        # Simply update the service in the registry
        for i, service in enumerate(service_registry["services"]):
            if service["service_id"] == service_id:
                service_registry["services"][i] = input_data
                break
        else:
            raise cherrypy.HTTPError(404, "Service not found")

        # Update last update of the whole register
        service_registry["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_service_registry(service_registry)

        return json.dumps({"status": "success", "message": "Service updated successfully"})

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
