import requests
from datetime import datetime

SERVICE_CATALOG_URL = "http://service_catalog:8080/services"
RESOURCE_CATALOG_URL = "http://resource_catalog:8081/devices"

# Function to register services
def register_service(config_dict):
    service = config_dict
    service["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        response = requests.post(SERVICE_CATALOG_URL, json=service)
        if response.status_code == 200:
            print(f"Service {service['service_id']} registered successfully.")
        else:
            print(f"Error registering the service: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during service registration: {e}")

# Function to delete services
def delete_service(service_id):
    try:
        # Send a DELETE request to the service catalog to remove the service
        response = requests.delete(f"{SERVICE_CATALOG_URL}/{service_id}")
        if response.status_code == 200:
            print(f"Service {service_id} deleted successfully.")
        elif response.status_code == 404:
            print(f"Service {service_id} not found.")
        else:
            print(f"Error deleting the service: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during service deletion: {e}")


# Function to register or update devices
def register_device(device_id, type, location, status, endpoint, time):
    device = {
        "device_id": device_id,
        "type": type,
        "location": location,
        "status": status,
        "endpoint": endpoint,
        "last_update": time
    }
    
    try:
        response = requests.post(RESOURCE_CATALOG_URL, json=device)
        if response.status_code == 200:
            print(f"Device {device['device_id']} registered successfully.")
        elif response.status_code == 409:
            try:
                response = requests.put(RESOURCE_CATALOG_URL, json=device)
                if response.status_code == 200:
                    print(f"Device {device['device_id']} updated successfully.")
            except requests.exceptions.RequestException as e:
                print(f"Connection error during device update: {e}")    
        else:
            print(f"Error registering/updating the device: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during device registration: {e}")
  
  
  
  
