import RPi.GPIO as GPIO
import time
import json
import requests
import datetime
import random

# GPIO setup for the real entrance button
entrance_button_pin = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(entrance_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# URL of the device connector
device_connector_url = "http://localhost:8082"

# Button press counters
entrance_count = 0
exit_count = 0

# Unique identifiers for the devices
entrance_device_id = "EntranceSensor001"  # Replace with your device ID
exit_device_id = "ExitSensor001"  # Replace with your device ID

# SenML record template for the entrance button
entrance_base_record = {
    "bn": "GymGenius/Occupancy/Entrance",  # Unique identifier for the entrance button
    "bt": 0,  # Base time
    "n": "push-button-enter",  # Sensor name
    "u": "count",  # Unit of measure
    "v": 0  # Value
}

# SenML record template for the exit button
exit_base_record = {
    "bn": "GymGenius/Occupancy/Exit",  # Unique identifier for the exit button
    "bt": 0,  # Base time
    "n": "push-button-exit",  # Sensor name
    "u": "count",  # Unit of measure
    "v": 0  # Value
}

# Function to send an entry event to the device connector
def send_entry_event():
    global entrance_count
    try:
        # Create the SenML record for entrance
        record = entrance_base_record.copy()
        record["bt"] = time.time()
        record["v"] = entrance_count

        # Send the record to the device connector as part of the POST request
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
            print(f"Entry event sent successfully: {entrance_count}")
        else:
            print(f"Error sending entry event: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

# Function to send an exit event to the device connector
def send_exit_event():
    global exit_count
    try:
        # Create the SenML record for exit
        record = exit_base_record.copy()
        record["bt"] = time.time()
        record["v"] = exit_count

        # Send the record to the device connector as part of the POST request
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
            print(f"Exit event sent successfully: {exit_count}")
        else:
            print(f"Error sending exit event: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

# Function to simulate exits
def simulate_exit():
    global exit_count, entrance_count
    # Ensure the number of exits is always less than or equal to entrances
    if exit_count < entrance_count:
        exit_count += 1
        send_exit_event()

# Main program
try:
    last_button_state = False
    while True:
        # Check the real entrance button
        button_state = GPIO.input(entrance_button_pin)
        if button_state != last_button_state:
            if button_state == False:  # Button pressed (active low)
                entrance_count += 1
                print(f"Button pressed (entrance): {entrance_count}")
                send_entry_event()

                # Simulate an exit after a random delay if possible
                if exit_count < entrance_count:
                    delay = random.uniform(5, 15)  # Random delay between 5 and 15 seconds
                    print(f"Simulating exit in {delay:.2f} seconds...")
                    time.sleep(delay)  # Wait for the delay
                    simulate_exit()

            last_button_state = button_state

        time.sleep(0.05)
except KeyboardInterrupt:
    GPIO.cleanup()
