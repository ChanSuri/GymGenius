import time
import board
import adafruit_dht
import json
import random
import requests
from datetime import datetime, timezone

# Initialization of the real DHT11 sensor
dhtDevice = adafruit_dht.DHT11(board.D15)

# Define rooms and assign real or simulated status
rooms = {
    "entrance": {"type": "real", "temperature": None, "humidity": None},
    "cardio_room": {"type": "simulated", "temperature": 22.0, "humidity": 50.0},
    "lifting_room": {"type": "simulated", "temperature": 23.0, "humidity": 52.0},
    "changing_room": {"type": "simulated", "temperature": 24.0, "humidity": 55.0}  # Updated for showers
}

# Set the unique sensor names for each room
file_names = {room: f"environment_{room}.json" for room in rooms}

# Device Connector URL
device_connector_url = "http://localhost:8082"

def gradual_change(current_value, min_value, max_value, step=0.5):
    """Simulate gradual changes in temperature or humidity within a given range."""
    change = random.uniform(-step, step)
    new_value = current_value + change
    return max(min(new_value, max_value), min_value)

def send_data_to_device_connector(room, temperature, humidity):
    """Send temperature and humidity data to the device connector."""
    try:
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Create the data payload to send
        data = {
            "device_id": f"DHT11_Sensor_{room}",  # Unique device ID for each room
            "event_type": "environment",  # Custom event type for environment data
            "type": "DHT11",  # Sensor type
            "location": room,  # Sensor location
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

        # Send POST request to device connector
        response = requests.post(device_connector_url, json=data)
        
        if response.status_code == 200:
            print(f"Data sent to device connector successfully for {room}")
        else:
            print(f"Error sending data for {room}: {response.status_code}, {response.text}")
    
    except Exception as e:
        print(f"Error in sending data to device connector for {room}: {e}")

try:
    while True:
        for room, sensor_info in rooms.items():
            current_time = datetime.now(timezone.utc).isoformat()
            
            if sensor_info["type"] == "real":
                # Read data from the real DHT11 sensor
                try:
                    temperature = dhtDevice.temperature
                    humidity = dhtDevice.humidity
                except RuntimeError as e:
                    print(f"Failed to retrieve data from real sensor in {room}: {e}")
                    continue
            else:
                # Gradually adjust the simulated data for temperature and humidity
                temperature = gradual_change(sensor_info["temperature"], 18, 30)
                humidity = gradual_change(sensor_info["humidity"], 40, 70)  # Adjusted to reflect showers in changing room

                # Update the current simulated values in the room dictionary
                sensor_info["temperature"] = temperature
                sensor_info["humidity"] = humidity

            if humidity is not None and temperature is not None:
                # Send data to the device connector
                send_data_to_device_connector(room, temperature, humidity)
                
                # Create the SenML payload and save locally
                data = [
                    {"bn": f"GymGenius/{room}/environment", 
                     "bt": current_time,
                     "n": "temperature",
                     "u": "Cel",
                     "v": temperature},

                    {"bn": f"GymGenius/{room}/environment",
                     "bt": current_time,
                     "n": "humidity",
                     "u": "%",
                     "v": humidity}
                ]
                
                # Convert to JSON and write to file
                json_data = json.dumps(data)
                with open(file_names[room], 'w') as file:
                    file.write(json_data)

                print(f"Data written to {file_names[room]}")
            else:
                print(f"Failed to retrieve data from {room}")

        # Wait for 5 minutes before the next reading
        time.sleep(300)

except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    dhtDevice.exit()
