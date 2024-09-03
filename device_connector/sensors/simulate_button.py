import requests
import time

device_connector_url = "http://localhost:8082"

for i in range(1, 11):  # Simula 10 pressioni
    data = {
        "device_id": "ExitSensor001",
        "event_type": "exit",
        "type": "push-button-exit",
        "location": "entrance",
        "status": "active",
        "endpoint": "GymGenius/Occupancy/Exit",
        "senml_record": {
            "bn": "GymGenius/Occupancy/Exit",
            "bt": time.time(),
            "n": "push-button-exit",
            "u": "count",
            "v": i
        }
    }
    response = requests.post(f"{device_connector_url}/", json=data)
    if response.status_code == 200:
        print(f"Simulated exit event {i} sent successfully")
    else:
        print(f"Error sending simulated exit event: {response.status_code}")
    time.sleep(2)  # Simula intervallo tra pressioni
