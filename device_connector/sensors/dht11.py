import time
import board
import adafruit_dht
import json
import requests
from datetime import datetime, timezone

# Initialization of the DHT11 sensor
dhtDevice = adafruit_dht.DHT11(board.D15)

# Set the unique name of the sensor (e.g., device name or location)
sensor_name = "GymGenius/entrance/environment"
file_name = "environment_entrance.json"

# Device Connector URL
device_connector_url = "http://localhost:8082"

def send_data_to_device_connector(temperature, humidity):
    """Send temperature and humidity data to the device connector."""
    try:
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Create the data payload to send
        data = {
            "device_id": "DHT11_Sensor",  # Unique device ID
            "event_type": "environment",  # Custom event type for environment data
            "type": "DHT11",  # Sensor type
            "location": "entrance",  # Sensor location
            "status": "active",
            "endpoint": "gym/environment",
            "time": current_time,
            "senml_record": {
                "bn": "gym/environment",
                "e": [
                    {"n": "temperature", "u": "Cel", "t": current_time, "v": temperature},
                    {"n": "humidity", "u": "%", "t": current_time, "v": humidity}
                ]
            }
        }

        # Send POST request to device connector
        response = requests.post(device_connector_url, json=data)
        
        if response.status_code == 200:
            print("Data sent to device connector successfully")
        else:
            print(f"Error sending data: {response.status_code}, {response.text}")
    
    except Exception as e:
        print(f"Error in sending data to device connector: {e}")

try:
    while True:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        current_time = datetime.now(timezone.utc).isoformat()

        if humidity is not None and temperature is not None:
            # Send data to the device connector
            send_data_to_device_connector(temperature, humidity)
            
            # Create the SenML payload and save locally (optional)
            data = [
                {"bn": sensor_name, 
                 "bt": current_time,
                 "n": "temperature",
                 "u": "Cel",
                 "v": temperature},

                {"bn": sensor_name,
                 "bt": current_time,
                 "n": "humidity",
                 "u": "%",
                 "v": humidity}
            ]
            
            # Convert to JSON and write to file
            json_data = json.dumps(data)
            with open(file_name, 'w') as file:
                file.write(json_data)

            print(f"Data written to {file_name}")
        else:
            print("Failed to retrieve data from humidity sensor")

        # Wait for 5 minutes before the next reading
        time.sleep(300)

except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    dhtDevice.exit()
