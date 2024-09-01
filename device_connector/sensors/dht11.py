import time
import board
import adafruit_dht
import json
from datetime import datetime, timezone

# Initialization of the DHT11 sensor
dhtDevice = adafruit_dht.DHT11(board.D15)

# Set the unique name of the sensor (e.g., device name or location)
sensor_name = "GymGenius/entrance/environment"
file_name = "environment_entrance.json"

try:
    while True:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        current_time = datetime.now(timezone.utc).isoformat()

        if humidity is not None and temperature is not None:
            # Create the SenML payload
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
            
            # Convert to JSON
            json_data = json.dumps(data)

            # Write the JSON data to the file
            with open(file_name, 'w') as file:
                file.write(json_data)
            
            # Print the file path and confirmation of write
            print(f"Data written to {file_name}")
        else:
            print("Failed to retrieve data from humidity sensor")

        time.sleep(2.0)

except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    dhtDevice.exit()
