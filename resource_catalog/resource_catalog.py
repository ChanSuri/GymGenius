import cherrypy
import json
import os
from datetime import datetime
from registration_functions import *
import signal

# Path to the device_registry.json file
# DEVICE_REGISTRY_FILE = 'C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\resource_catalog\\device_registry.json'
DEVICE_REGISTRY_FILE = 'device_registry.json'

def load_device_registry():
    """Loads the device registry from the file."""
    if os.path.exists(DEVICE_REGISTRY_FILE):
        with open(DEVICE_REGISTRY_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_device_registry(registry):
    """Saves the device registry to the file."""
    with open(DEVICE_REGISTRY_FILE, 'w') as file:
        json.dump(registry, file, indent=4)

# Load the device registry from the file at startup
device_registry = load_device_registry()

class ResourceCatalog:
    exposed = True
    
    def __init__(self, config):
        self.config = config
        self.service_catalog_url = config['service_catalog']  # Get service catalog URL from config.json


    def GET(self, *uri, **params):
        # If device_id is provided in the URI, return the specific device
        if len(uri) > 0:
            device_id = uri[0]
            device = next((d for d in device_registry.get("devices", []) if d["device_id"] == device_id), None) #next return the first matching device
            if device:
                return json.dumps({"status": "success", "device": device})
            else:
                raise cherrypy.HTTPError(404, "Device not found")
        else:
            # Return all registry if no device_id is provided
            return json.dumps({"status": "success", "devices": device_registry})


    def POST(self, *uri, **params):
        # Read and decode the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)
        device_id = input_data.get("device_id")

        # Ensure device_id is present
        if not device_id:
            raise cherrypy.HTTPError(400, "device_id is required")

        # Build a dictionary for quick lookup
        devices_by_id = {device["device_id"]: device for device in device_registry["devices"]}

        # Check if the device already exists
        if device_id in devices_by_id:
            existing_device = devices_by_id[device_id]
            if input_data == existing_device:
                raise cherrypy.HTTPError(304, "Device already registered with the same data")
            else:
                raise cherrypy.HTTPError(409, "Device exists but data differs. Update required.")

        # Add the device to the registry
        device_registry["devices"].append(input_data)
        
        # update last update of the whole register 
        device_registry["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_device_registry(device_registry)
        return json.dumps({"status": "success", "message": "Device registered successfully"})


    def PUT(self, *uri, **params):
        # Read and decode the request body
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)
        device_id = input_data.get("device_id")

        # Ensure device_id is present
        if not device_id:
            raise cherrypy.HTTPError(400, "device_id is required")

        # Simply update the device in the registry
        for i, device in enumerate(device_registry["devices"]):
            if device["device_id"] == device_id:
                device_registry["devices"][i] = input_data
                break
        else: # else with for cicle is used when the cicle ends without a break
            raise cherrypy.HTTPError(404, "Device not found")

        # Update last update of the whole register
        device_registry["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_device_registry(device_registry)
        
        return json.dumps({"status": "success", "message": "Device updated successfully"})


    def DELETE(self, *uri, **params):
        # Ensure device_id is provided in the URI
        if len(uri) == 0:
            raise cherrypy.HTTPError(400, "device_id is required")

        device_id = uri[0]

        # Check if the device exists in the registry
        for i, device in enumerate(device_registry["devices"]):
            if device["device_id"] == device_id:
                # Remove the device from the registry
                del device_registry["devices"][i]
                
                # Update lastUpdate
                device_registry["lastUpdate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_device_registry(device_registry)
                return json.dumps({"status": "success", "message": f"Device {device_id} deleted successfully"})
        
        # If no matching device was found
        raise cherrypy.HTTPError(404, "Device not found")
    
def initialize_service(config_dict):
    # Register the service at startup
    register_service(config_dict,service.service_catalog_url)
    print("Resource Catalog Service Initialized and Registered")

def stop_service(signum, frame):
    print("\n[INFO] SIGINT received: Stopping Resource Catalog...")
    try:
        delete_service(service.config["service_id"], service.service_catalog_url)
        print("[INFO] Service successfully deregistered from Service Catalog.")
    except Exception as e:
        print(f"[WARNING] Failed to deregister service: {e}")

    cherrypy.engine.exit()

if __name__ == '__main__':

    # with open('C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\resource_catalog\\config_resource_catalog.json') as config_file:
    with open('config_resource_catalog.json') as config_file:
        config = json.load(config_file)
    
    service = ResourceCatalog(config)
    initialize_service(config)
    
    # Configure the MethodDispatcher and session management
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }

    # Update CherryPy configuration with port and host settings
    cherrypy.config.update({'server.socket_port': 8081, 'server.socket_host': '0.0.0.0'})
    
    # Mount the ResourceCatalog class using MethodDispatcher
    cherrypy.tree.mount(service, '/', conf)
    
    # Clean stop
    signal.signal(signal.SIGINT, stop_service)   # Ctrl+C
    signal.signal(signal.SIGTERM, stop_service)  # From OS

    # Start the CherryPy server
    cherrypy.engine.start()
    cherrypy.engine.block()
