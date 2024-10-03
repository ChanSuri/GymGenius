import time
import json
import requests
import datetime
import random

# URL del Device Connector
#device_connector_url = "http://localhost:8082"
device_connector_url = "http://device_connector:8082"

# Contatori per i pulsanti di ingresso e uscita
entrance_count = 0
exit_count = 0

# ID unici per i dispositivi simulati
entrance_device_id = "EntranceSensor001"
exit_device_id = "ExitSensor001"

# Record SenML simulati per i pulsanti
entrance_base_record = {
    "bn": "GymGenius/Occupancy/Entrance",
    "bt": 0,
    "n": "push-button-enter",
    "u": "count",
    "v": 0
}

exit_base_record = {
    "bn": "GymGenius/Occupancy/Exit",
    "bt": 0,
    "n": "push-button-exit",
    "u": "count",
    "v": 0
}

# Funzione per simulare un evento di ingresso
def send_entry_event():
    global entrance_count
    entrance_count += 1
    try:
        # Crea il record SenML per l'ingresso
        record = entrance_base_record.copy()
        record["bt"] = time.time()
        record["v"] = entrance_count

        # Invia il record al Device Connector
        data = {
            "device_id": entrance_device_id,
            "event_type": "entry",
            "type": record["n"],
            "location": "entrance",
            "status": "active",
            "endpoint": record["bn"],
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "senml_record": record
        }
        response = requests.post(f"{device_connector_url}/", json=data)
        if response.status_code == 200:
            print(f"Evento di ingresso inviato con successo: {entrance_count}")
        else:
            print(f"Errore nell'invio dell'evento di ingresso: {response.status_code}")
    except Exception as e:
        print(f"Errore: {e}")

# Funzione per simulare un evento di uscita
def send_exit_event():
    global exit_count, entrance_count
    if exit_count < entrance_count:  # Assicura che le uscite non superino gli ingressi
        exit_count += 1
        try:
            # Crea il record SenML per l'uscita
            record = exit_base_record.copy()
            record["bt"] = time.time()
            record["v"] = exit_count

            # Invia il record al Device Connector
            data = {
                "device_id": exit_device_id,
                "event_type": "exit",
                "type": record["n"],
                "location": "entrance",
                "status": "active",
                "endpoint": record["bn"],
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "senml_record": record
            }
            response = requests.post(f"{device_connector_url}/", json=data)
            if response.status_code == 200:
                print(f"Evento di uscita inviato con successo: {exit_count}")
            else:
                print(f"Errore nell'invio dell'evento di uscita: {response.status_code}")
        except Exception as e:
            print(f"Errore: {e}")

# Funzione principale per simulare ingressi ed uscite
def simulate_button_events():
    while True:
        send_entry_event()  # Simula un ingresso
        time.sleep(random.uniform(1, 5))  # Simula una pausa tra 1 e 5 secondi
        send_exit_event()  # Simula un'uscita
        time.sleep(random.uniform(5, 10))  # Simula una pausa tra 5 e 10 secondi

if __name__ == "__main__":
    try:
        simulate_button_events()
    except KeyboardInterrupt:
        print("Simulazione interrotta dall'utente.")
