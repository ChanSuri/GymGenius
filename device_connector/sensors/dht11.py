import time
import board
import adafruit_dht
import json
from datetime import datetime, timezone

# Inizializzazione del sensore DHT11
dhtDevice = adafruit_dht.DHT11(board.D15)

# Imposta il nome univoco del sensore (ad esempio, il nome del dispositivo o una posizione)
sensor_name = "GymGenius/entrance/environment"
file_name = "environment_entrance.json"

try:
    while True:
        temperature = dhtDevice.temperature
        humidity = dhtDevice.humidity
        current_time = datetime.now(timezone.utc).isoformat()

        if humidity is not None and temperature is not None:
            # Creazione del payload SenML
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
            
            # Conversione in JSON
            json_data = json.dumps(data)

            # Scrive i dati JSON nel file
            with open(file_name, 'w') as file:
                file.write(json_data)
            
            # Stampa il percorso del file e la conferma di scrittura
            print(f"Dati scritti in {file_name}")
        else:
            print("Failed to retrieve data from humidity sensor")

        time.sleep(2.0)

except KeyboardInterrupt:
    print("Program stopped by user")
finally:
    dhtDevice.exit()

