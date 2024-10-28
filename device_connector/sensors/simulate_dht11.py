#This is script is used only to test the service without the raspberry

import time
import json
import random
import requests
from datetime import datetime, timezone

# Definizione delle stanze e della loro temperatura/umidità simulata
rooms = {
    "entrance": {"type": "simulated", "temperature": 16.5, "humidity": 50.0},
    "cardio_room": {"type": "simulated", "temperature": 20.0, "humidity": 50.0},
    "lifting_room": {"type": "simulated", "temperature": 20.0, "humidity": 52.0},
    "changing_room": {"type": "simulated", "temperature": 24.0, "humidity": 55.0}
}

# URL del Device Connector
# device_connector_url = "http://localhost:8082"
device_connector_url = "http://device_connector:8082"

def gradual_change(current_value, min_value, max_value, step=0.5):
    """Simula cambiamenti graduali di temperatura o umidità entro un range definito."""
    change = random.uniform(-step, step)
    new_value = current_value + change
    return max(min(new_value, max_value), min_value)

def send_data_to_device_connector(room, temperature, humidity):
    """Invia i dati simulati al Device Connector."""
    try:
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Crea il payload da inviare
        data = {
            "device_id": f"DHT11_Sensor_{room}",
            "event_type": "environment",
            "type": "DHT11",
            "location": room,
            "status": "active",
            "endpoint": f"gym/environment/{room}",
            "time": current_time,
            "senml_record": {
                "bn": f"gym/environment/{room}",
                "e": [
                    {"n": "temperature", "u": "Cel", "t": current_time, "v": temperature},
                    {"n": "humidity", "u": "%", "t": current_time, "v": humidity}
                ]
            }
        }

        # Invia i dati al Device Connector
        response = requests.post(device_connector_url, json=data)
        
        if response.status_code == 200:
            print(f"Dati inviati con successo per {room}")
        else:
            print(f"Errore nell'invio dei dati per {room}: {response.status_code}, {response.text}")
    
    except Exception as e:
        print(f"Errore nell'invio dei dati per {room}: {e}")

# Funzione principale per simulare i sensori DHT11
def simulate_dht11_sensors():
    while True:
        for room, sensor_info in rooms.items():
            temperature = gradual_change(sensor_info["temperature"], 13, 30)
            humidity = gradual_change(sensor_info["humidity"], 40, 70)

            # Aggiorna i valori simulati
            sensor_info["temperature"] = temperature
            sensor_info["humidity"] = humidity

            # Invia i dati al Device Connector
            send_data_to_device_connector(room, temperature, humidity)

        time.sleep(30)  # Simula un intervallo di 5 minuti tra le letture

if __name__ == "__main__":
    try:
        simulate_dht11_sensors()
    except KeyboardInterrupt:
        print("Simulazione interrotta dall'utente.")
