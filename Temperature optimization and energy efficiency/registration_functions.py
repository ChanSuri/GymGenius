import requests

SERVICE_CATALOG_URL = "http://localhost:8080/services"
RESOURCE_CATALOG_URL = "http://localhost:8081/devices"

# Funzione per registrare i servizi
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
            print(f"Servizio {service['service_id']} registrato correttamente.")
        else:
            print(f"Errore nella registrazione del servizio: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione durante la registrazione del servizio: {e}")

# Funzione per registrare i dispositivi
def register_device(device_id, type, location, status, endpoint):
    device = {
        "device_id": device_id,
        "type": type,
        "location": location,
        "status": status,
        "endpoint": endpoint
    }
    
    try:
        response = requests.post(RESOURCE_CATALOG_URL, json=device)
        if response.status_code == 200:
            print(f"Dispositivo {device['device_id']} registrato correttamente.")
        else:
            print(f"Errore nella registrazione del dispositivo: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione durante la registrazione del dispositivo: {e}")
