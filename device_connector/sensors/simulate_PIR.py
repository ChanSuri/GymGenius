#This is script is used only to test the service without the raspberry

import time
import json
import requests
from datetime import datetime
import random

# URL del Device Connector
#device_connector_url = "http://localhost:8082"
device_connector_url = "http://device_connector:8082"

# Definizione delle macchine simulate
cardio_machines = ["treadmill", "elliptical_trainer", "stationary_bike"]
lifting_machines = ["rowing_machine", "cable_machine", "leg_press_machine", "smith_machine", "lat_pulldown_machine"]

# Funzione per inviare i dati al Device Connector
def send_data_to_device_connector(value, machine, room, machine_number):
    record = {
        "bn": f"GymGenius/Occupancy/Availability/{machine}/{machine_number}",
        "bt": 0,
        "n": machine,
        "u": "binary",
        "v": value
    }

    data = {
        "device_id": f"simulated_{machine}_{machine_number}",
        "event_type": "availability",
        "type": record["n"],
        "location": room,
        "status": "active" if value == 1 else "inactive",
        "endpoint": record["bn"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "senml_record": record
    }

    try:
        response = requests.post(device_connector_url, json=data)
        if response.status_code == 200:
            print(f"Dati inviati per {machine} {machine_number} nel {room}.")
        else:
            print(f"Errore nell'invio dei dati per {machine} {machine_number}: {response.status_code}")
    except Exception as e:
        print(f"Errore nell'invio della richiesta: {e}")

# Funzione per simulare l'uso delle macchine
def simulate_machine_usage(machine_list, room):
    while True:
        for machine_index, machine in enumerate(machine_list, start=1):
            # Simula casualmente l'occupazione (1 = occupata, 0 = disponibile)
            simulated_value = random.choice([0, 1])
            send_data_to_device_connector(simulated_value, machine, room, machine_index)
            time.sleep(random.randint(5, 10))  # Simula intervalli casuali tra i cambiamenti di stato

if __name__ == "__main__":
    try:
        simulate_machine_usage(cardio_machines, "cardio room")
        simulate_machine_usage(lifting_machines, "lifting room")
    except KeyboardInterrupt:
        print("Simulazione interrotta dall'utente.")
