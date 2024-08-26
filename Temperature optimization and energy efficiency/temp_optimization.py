import cherrypy
import paho.mqtt.client as mqtt
import json
import time
import requests
from datetime import datetime, timedelta
import signal
from registration_functions import register_service

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_env = "gym/environment"
mqtt_topic_control = "gym/hvac/control"
mqtt_topic_threshold = "gym/threshold"  # Topic for thresholds update
mqtt_topic_occupancy = "gym/occupancy/current"  # Topic for current occupancy

# Thingspeak Configuration
thingspeak_write_api_key = "YOUR_THINGSPEAK_WRITE_API_KEY"
thingspeak_url = "https://api.thingspeak.com/update"

class TempOptimizationService:
    exposed = True

    def __init__(self, gym_schedule):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        self.client.subscribe(mqtt_topic_env)
        self.client.subscribe(mqtt_topic_threshold)  # Subscribing to threshold topic
        self.client.subscribe(mqtt_topic_occupancy)  # Subscribing to occupancy topic

        self.gym_schedule = gym_schedule
        self.thresholds = {'upper': 28, 'lower': 24}  # Default thresholds
        self.hvac_state = 'off'
        self.current_occupancy = 0  # Initialize the occupancy to 0

    def connect_mqtt(self):
        try:
            self.client.connect(mqtt_broker, 1883, 60)
            print("MQTT connected successfully.")
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            time.sleep(5)
            self.connect_mqtt()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
        else:
            print(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with return code {rc}. Reconnecting...")
        self.connect_mqtt()

    def on_message(self, client, userdata, message):
        if message.topic == mqtt_topic_env:
            data = json.loads(message.payload.decode())
            temperature = data.get('temperature')
            humidity = data.get('humidity')

            if temperature is not None and humidity is not None:
                print(f"Received temperature: {temperature}°C, humidity: {humidity}%")
                self.control_hvac(temperature, humidity)
                self.send_data_to_thingspeak(temperature, humidity)
        
        elif message.topic == mqtt_topic_threshold:  # Handle threshold updates via MQTT
            try:
                threshold_data = json.loads(message.payload.decode())
                upper = threshold_data.get('upper')
                lower = threshold_data.get('lower')

                # Validate and set the thresholds with bounds
                if upper is not None and isinstance(upper, (int, float)):
                    self.thresholds['upper'] = max(15, min(upper, 35))  # Limit thresholds to realistic values
                if lower is not None and isinstance(lower, (int, float)):
                    self.thresholds['lower'] = max(15, min(lower, 35))

                print(f"Updated thresholds: upper = {self.thresholds['upper']}°C, lower = {self.thresholds['lower']}°C")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to decode threshold data: {e}")

        elif message.topic == mqtt_topic_occupancy:  # Handle occupancy updates via MQTT
            try:
                occupancy_data = json.loads(message.payload.decode())
                self.current_occupancy = occupancy_data.get('occupancy', 0)
                print(f"Received occupancy data: {self.current_occupancy} clients present.")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to decode occupancy data: {e}")

    def control_hvac(self, temperature, humidity):
        current_time = datetime.now()
        is_open = self.gym_schedule['open'] <= current_time.time() <= self.gym_schedule['close']

        # Turn on HVAC in advance to prepare the gym environment
        advance_time = timedelta(minutes=30)
        open_time_with_advance = (datetime.combine(datetime.today(), self.gym_schedule['open']) - advance_time).time()
        
        # Check if the HVAC needs to be turned on in advance
        if open_time_with_advance <= current_time.time() <= self.gym_schedule['close']:
            is_open = True

        # Check for automatic shutdown 30 minutes before closing time if no clients are present
        close_time_with_advance = (datetime.combine(datetime.today(), self.gym_schedule['close']) - advance_time).time()
        if current_time.time() >= close_time_with_advance and self.current_occupancy == 0:
            if self.hvac_state == 'on':
                print("No clients present 30 minutes before closing. Turning off HVAC.")
                self.hvac_state = 'off'
                self.send_hvac_command('turn_off')
            return

        # Control based on temperature and gym hours
        if is_open and self.hvac_state == 'off' and temperature > self.thresholds['upper']:
            self.hvac_state = 'on'
            self.send_hvac_command('turn_on')
        elif not is_open and self.hvac_state == 'on':
            self.hvac_state = 'off'
            self.send_hvac_command('turn_off')

    def send_hvac_command(self, command):
        payload = json.dumps({"command": command})
        self.client.publish(mqtt_topic_control, payload)
        print(f"Sent HVAC command: {command}")

    def send_data_to_thingspeak(self, temperature, humidity):
        try:
            response = requests.post(thingspeak_url, data={
                'api_key': thingspeak_write_api_key,
                'field1': temperature,
                'field2': humidity
            })
            if response.status_code == 200:
                print("Data sent to Thingspeak successfully.")
            else:
                print(f"Failed to send data to Thingspeak. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending data to Thingspeak: {e}")

    # REST API to retrieve current HVAC status
    def GET(self, *uri, **params):
        return json.dumps({
            "status": "success",
            "hvac_state": self.hvac_state,
            "thresholds": self.thresholds,
            "occupancy": self.current_occupancy
        })

    def stop(self):
        self.client.loop_stop()
        print("MQTT client stopped.")


def initialize_service():
    # Register the service at startup
    service_id = "hvac_control"
    description = "Gestione e controllo HVAC"
    status = "active"
    endpoint = "http://localhost:8083/hvac"
    register_service(service_id, description, status, endpoint)
    print("Temperature Optimization Service Initialized and Registered")

def stop_service(signum, frame):
    print("Stopping service...")
    cherrypy.engine.exit()

    # Clean stop of the MQTT client
    service.stop()


if __name__ == "__main__":
    gym_schedule = {'open': datetime.strptime('08:00', '%H:%M').time(),
                    'close': datetime.strptime('24:00', '%H:%M').time()}

    # Inizializzazione del servizio
    service = TempOptimizationService(gym_schedule)
    initialize_service()

    # Gestore di segnale per arresto pulito
    signal.signal(signal.SIGINT, stop_service)
    
    # Configurazione di CherryPy per esporre l'API REST
    cherrypy.config.update({'server.socket_port': 8083, 'server.socket_host': '0.0.0.0'})
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    }

    # Avvio del servizio
    cherrypy.tree.mount(service, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
