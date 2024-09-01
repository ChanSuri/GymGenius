import requests

SERVICE_CATALOG_URL = "http://localhost:8080/services"
RESOURCE_CATALOG_URL = "http://localhost:8081/devices"

# Function to register services
def register_service(service_id, description, status, endpoint):
    service = {
        "service_id": service_id,
        "description": description,
        "status": status,
        "endpoint": endpoint
    }
    
    try:
        response = requests.post(SERVICE_CATALOG_URL, json=service)
        if response.status_code == 200:
            print(f"Service {service['service_id']} registered successfully.")
        else:
            print(f"Error registering the service: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Connection error during service registration: {e}")

# Function to register or update devices
def register_device(device_id, type, location, status, endpoint, time):
    device = {
        "device_id": device_id,
        "type": type,
        "location": location,
        "status": status,
        "endpoint": endpoint,
        "time": time
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
