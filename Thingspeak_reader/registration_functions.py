import requests
from datetime import datetime

# Function to register or update services
def register_service(config_dict, service_catalog_url):
    service = config_dict
    service["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        response = requests.post(service_catalog_url, json=service)
        if response.status_code == 200:
            print(f"Service {service['service_id']} registered successfully.")
        elif response.status_code == 409:  # Conflict, service already exists
            try:
                # Perform PUT request to update the service
                response = requests.put(service_catalog_url, json=service)
                if response.status_code == 200:
                    print(f"Service {service['service_id']} updated successfully.")
                else:
                    print(f"Error updating the service: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Connection error during service update: {e}")
        else:
            print(f"Error registering the service: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during service registration: {e}")

# Function to delete services
def delete_service(service_id, service_catalog_url):
    try:
        # Send a DELETE request to the service catalog to remove the service
        response = requests.delete(f"{service_catalog_url}/{service_id}")
        if response.status_code == 200:
            print(f"Service {service_id} deleted successfully.")
        elif response.status_code == 404:
            print(f"Service {service_id} not found.")
        else:
            print(f"Error deleting the service: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during service deletion: {e}")

# Function to register or update devices
def register_device(device_id, type, location, status, endpoint, time, resource_catalog_url):
    device = {
        "device_id": device_id,
        "type": type,
        "location": location,
        "status": status,
        "endpoint": endpoint,
        "last_update": time
    }
    
    try:
        response = requests.post(resource_catalog_url, json=device)
        if response.status_code == 200:
            print(f"Device {device['device_id']} registered successfully.")
        elif response.status_code == 409:
            try:
                response = requests.put(resource_catalog_url, json=device)
                if response.status_code == 200:
                    print(f"Device {device['device_id']} updated successfully.")
            except requests.exceptions.RequestException as e:
                print(f"Connection error during device update: {e}")    
        else:
            print(f"Error registering/updating the device: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during device registration: {e}")
