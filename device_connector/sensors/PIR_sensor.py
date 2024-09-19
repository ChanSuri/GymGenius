import RPi.GPIO as GPIO
import time
import json
import requests
from datetime import datetime
import random

# PIR sensor PIN configuration (per il sensore reale)
PIR_PIN = 11  # Pin 11 corresponds to GPIO 17
device_connector_url = "http://localhost:8082"  # URL of the Device Connector

GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIR_PIN, GPIO.IN)

# Definition of data to be sent for treadmill 1 (sensore reale)
device_id_real = "PIR_treadmill_1"  # Unique device ID for the real sensor

# Funzione per inviare dati al device connector
def send_data_to_device_connector(value, device_name, room, device_id):
    """Send PIR sensor or simulated data to the device connector."""
    record = {
        "bn": f"GymGenius/Occupancy/Availability/{device_name}/1",
        "bt": 0,
        "n": device_name,
        "u": "binary",
        "v": value
    }

    data = {
        "device_id": device_id,
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
            print(f"Data for {device_name} successfully sent to the device connector.")
        else:
            print(f"Error sending data for {device_name}: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending the request: {e}")

# Simulazione per le altre macchine
def simulate_machine_usage(machine_list, room):
    """Simulates occupancy for the machines in a room."""
    while True:
        for machine in machine_list:
            # Randomly simulate occupancy (1 = occupied, 0 = available)
            simulated_value = random.choice([0, 1])
            send_data_to_device_connector(simulated_value, machine, room, f"simulated_{machine}")
            time.sleep(random.randint(5, 10))  # Simulate random intervals between state changes

# Funzione per gestire il sensore PIR reale
def handle_real_pir_sensor():
    """Handles the real PIR sensor for treadmill 1."""
    try:
        time.sleep(2)  # Wait for the sensor to stabilize
        print("Ready to detect movement on treadmill 1...")

        previous_state = GPIO.input(PIR_PIN)  # Read the initial state of the sensor

        while True:
            current_state = GPIO.input(PIR_PIN)  # Read the current state of the sensor

            if current_state != previous_state:  # Send request only when there's a state change
                print(f"Sensor state changed: {current_state}")
                send_data_to_device_connector(current_state, "treadmill", "cardio room", device_id_real)
                previous_state = current_state  # Update previous state

            time.sleep(1)

    except KeyboardInterrupt:
        print("Real PIR sensor handling interrupted by the user")

    finally:
        GPIO.cleanup()

# Lista delle macchine simulate
cardio_machines = ["elliptical_trainer", "stationary_bike"]
lifting_machines = ["rowing_machine", "cable_machine", "leg_press_machine", "smith_machine", "lat_pulldown_machine"]

print("Starting simulation and real sensor monitoring... (CTRL+C to stop)")

try:
    # Esegui il sensore PIR reale e la simulazione in parallelo
    import threading
    # Thread per il sensore PIR reale
    real_sensor_thread = threading.Thread(target=handle_real_pir_sensor)
    real_sensor_thread.start()

    # Thread per la simulazione delle macchine
    simulate_machine_usage(cardio_machines, "cardio room")
    simulate_machine_usage(lifting_machines, "lifting room")

except KeyboardInterrupt:
    print("Simulation interrupted by user.")
finally:
    GPIO.cleanup()



# import RPi.GPIO as GPIO
# import time

# PIR_PIN = 11  # Pin 11 corrisponde a GPIO 17

# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(PIR_PIN, GPIO.IN)

# print("Test del sensore PIR (CTRL+C per terminare)")

# try:
#     time.sleep(2)  # Attendi che il sensore si stabilizzi
#     print("Pronto per rilevare movimento...")
#     while True:
#         pir_state = GPIO.input(PIR_PIN)  # Leggi lo stato del sensore
#         print(f"Stato sensore: {pir_state}")  # Mostra il valore grezzo del sensore
#         if pir_state:
#             print("Movimento rilevato!")
#             time.sleep(5)  # Aggiungi un'attesa di 5 secondi per vedere se si ripristina
#         else:
#             print("Nessun movimento")
#         time.sleep(1)

# except KeyboardInterrupt:
#     print("Test interrotto dall'utente")

# finally:
#     GPIO.cleanup()