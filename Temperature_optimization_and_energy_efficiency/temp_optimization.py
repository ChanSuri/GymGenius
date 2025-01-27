import paho.mqtt.client as mqtt
import json
import time
import requests
from datetime import datetime, timedelta
import signal
from registration_functions import *

class TempOptimizationService:
    def __init__(self, config):
        self.config = config
        self.service_catalog_url = config['service_catalog']  # Get service catalog URL from config.json
        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()  # Retrieve broker and port
        self.thresholds = self.get_thresholds_from_service_catalog()
        self.alert_temperature = self.get_alert_thresholds_from_service_catalog('temperature_alert_thresholds')
        self.alert_humidity = self.get_alert_thresholds_from_service_catalog('humidity_alert_thresholds')
        self.gym_schedule = self.get_gym_schedule_from_service_catalog()  # Get gym schedule from service catalog

        self.client = mqtt.Client()
        try:
            self.client.on_connect = self.on_connect
        except Exception as e:
            print(f"Error in MQTT loop: {e}")
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        # Subscribe to topics from config.json
        # self.subscribe_to_topics()

        self.hvac_state = {room: 'off' for room in self.thresholds.keys()}
        self.current_occupancy = 0
        self.current_command = {room: "AUTOMATIC" for room in self.thresholds.keys()}  # Default command state is ON for each room

    def get_mqtt_info_from_service_catalog(self):
        """Retrieve MQTT broker and port information from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('brokerIP'), catalog.get('brokerPort')  # Return both broker IP and port
            else:
                raise Exception(f"Failed to get broker information: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting MQTT info from service catalog: {e}")
            return None, None


    def get_thresholds_from_service_catalog(self):
        """Retrieve temperature thresholds for all rooms from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('temperature_default_thresholds')
            else:
                raise Exception(f"Failed to get temperature thresholds: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving thresholds from service catalog: {e}")
            return {}

    def get_alert_thresholds_from_service_catalog(self, threshold_type):
        """Retrieve alert thresholds (temperature or humidity) from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get(threshold_type)
            else:
                raise Exception(f"Failed to get alert thresholds: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving alert thresholds from service catalog: {e}")
            return {}
        
    def get_gym_schedule_from_service_catalog(self):
        """Retrieve gym schedule from the service catalog."""
        try:
            # Request to the service catalog
            response = requests.get(self.service_catalog_url, timeout=5)
            
            # Check if the response was successful
            if response.status_code == 200:
                print("Response received from service catalog.")
                service_catalog = response.json()

                catalog = service_catalog.get('catalog', {})

                # Verifica la presenza del campo 'time_slots' nel JSON
                time_slots = catalog.get('time_slots', None)
                if time_slots is None:
                    raise ValueError("time_slots is missing in the service catalog response")

                # Stampa i time_slots per assicurarsi che i dati siano corretti
                print(f"time_slots: {time_slots}")
                
                # Check if specific time slots exist
                if '0' in time_slots and '7' in time_slots:
                    gym_schedule = {
                        'open': datetime.strptime(time_slots['0']['start'], '%H:%M').time(),
                        'close': datetime.strptime(time_slots['7']['end'], '%H:%M').time()
                    }
                    print(f"Gym schedule retrieved: Open at {gym_schedule['open']}, Close at {gym_schedule['close']}")
                    return gym_schedule
                else:
                    raise ValueError("Missing required time slots ('0' or '7') in the service catalog.")
            else:
                raise Exception(f"Failed to get gym schedule: {response.status_code}")
        except (requests.exceptions.RequestException, ValueError) as e:
            # Log the error and notify about fallback
            print(f"Error retrieving gym schedule from service catalog: {e}")
            print("Using fallback gym schedule (08:00 to 23:59)")
            # Return fallback schedule
            return {
                'open': datetime.strptime('08:00', '%H:%M').time(),
                'close': datetime.strptime('23:59', '%H:%M').time()
            }


    def connect_mqtt(self):
        """Connect to the MQTT broker."""
        try:
            if self.mqtt_broker:
                self.client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
                print("MQTT connected successfully.")
            else:
                print("No MQTT broker information found.")
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            time.sleep(5)
            self.connect_mqtt()

    def on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            print("Connected to MQTT broker.")
            self.subscribe_to_topics()
        else:
            print(f"Failed to connect to MQTT broker. Return code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        print(f"Disconnected from MQTT broker with return code {rc}. Reconnecting...")
        self.connect_mqtt()

    def subscribe_to_topics(self):
        """Subscribe to topics listed in the config file."""
        try:
            for topic_key, topic_value in self.config["subscribed_topics"].items():
                self.client.subscribe(topic_value)
                print(f"Subscribed to topic: {topic_value}")
        except KeyError as e:
            print(f"Error in subscribed_topics format: {e}")

    def on_message(self, client, userdata, message):
        """Handle received MQTT messages."""
        for room in self.thresholds.keys():
            if message.topic.startswith(self.config['subscribed_topics']['enviroment'].replace('#', room)):
                self.handle_environment_data(room, message)
            elif message.topic.startswith(self.config['subscribed_topics']['desired_temperature'].replace('#', room)):
                self.handle_desired_temperature(room, message)
            elif message.topic.startswith(self.config['subscribed_topics']['control_commands'].replace('#', room)):
                self.handle_hvac_on_off(room, message)

        if message.topic == self.config['subscribed_topics']['current_occupancy']:
            self.handle_occupancy(message)

    def handle_environment_data(self, room, message):
        """Handle environment data (temperature and humidity) for a specific room."""
        try:
            data = json.loads(message.payload.decode())
            events = data.get('e', [])

            temperature = None
            humidity = None

            # Parse the JSON to extract temperature and humidity values
            for event in events:
                if event.get('n') == 'temperature':
                    temperature = event.get('v')
                elif event.get('n') == 'humidity':
                    humidity = event.get('v')

            if temperature is not None and humidity is not None:
                print(f"[{room}] Received temperature: {temperature}°C, humidity: {humidity}%")
                self.control_hvac(room, temperature, humidity)
                self.check_alerts(room, temperature, humidity)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to decode environment data for {room}: {e}")

    def handle_desired_temperature(self, room, message):
        """Handle desired temperature updates for a specific room."""
        try:
            threshold_data = json.loads(message.payload.decode())
            desired_temperature = threshold_data['message']['data'].get('desired_temperature')
            upper = desired_temperature + 1
            lower = desired_temperature - 1

            # Validate and set the thresholds with bounds
            if upper is not None and isinstance(upper, (int, float)):
                self.thresholds[room]['upper'] = max(15, min(upper, 35))  # Limit thresholds to realistic values
            if lower is not None and isinstance(lower, (int, float)):
                self.thresholds[room]['lower'] = max(15, min(lower, 35))

            print(f"[{room}] Updated desired temperature: {desired_temperature}°C, upper = {self.thresholds[room]['upper']}°C, lower = {self.thresholds[room]['lower']}°C")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to decode threshold data for {room}: {e}")

    def handle_hvac_on_off(self, room, message):
        """Handle HVAC on/off commands for a specific room."""
        try:
            command_data = json.loads(message.payload.decode())
            self.current_command[room] = command_data['message']['data'].get('state', "ON").upper()
            print(f"[{room}] Received administrator command: {self.current_command[room]}.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to decode command data for {room}: {e}")

    def handle_occupancy(self, message):
        """Handle occupancy data."""
        try:
            occupancy_data = json.loads(message.payload.decode())
            self.current_occupancy = occupancy_data['message']['data'].get('current_occupancy', 0)
            print(f"Received occupancy data: {self.current_occupancy} clients present.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to decode occupancy data: {e}")

    def control_hvac(self, room, temperature, humidity):
        """Control the HVAC system based on temperature, humidity, and occupancy."""
        ### DA CAPIRE PERCHE' DI DEFAULT OFF O ON
        print(self.current_command[room])
        if self.current_command[room] == "OFF" or self.current_command[room] == "ON":
            print(f"[{room}] Automatic HVAC control disabled by administrator.")
            return

        current_time = datetime.now()
        is_open = self.gym_schedule['open'] <= current_time.time() <= self.gym_schedule['close']

        # Turn on HVAC in advance to prepare the gym environment
        advance_time = timedelta(minutes=30)
        open_time_with_advance = (datetime.combine(datetime.today(), self.gym_schedule['open']) - advance_time).time()

        if open_time_with_advance <= current_time.time() <= self.gym_schedule['close']:
            is_open = True

        close_time_with_advance = (datetime.combine(datetime.today(), self.gym_schedule['close']) - advance_time).time()
        if current_time.time() >= close_time_with_advance and self.current_occupancy == 0:
            if self.hvac_state[room] == 'on':
                print(f"[{room}] No clients present 30 minutes before closing. Turning off HVAC.")
                self.hvac_state[room] = 'off'
                self.send_hvac_command(room, 'turn_off')
            return

        # Control based on temperature and gym hours
        if is_open and self.hvac_state[room] == 'off':
            if temperature > self.thresholds[room]['upper']:
                self.hvac_state[room] = 'on'
                self.send_hvac_command(room, 'turn_on', 'cool')
            elif temperature < self.thresholds[room]['lower']:
                self.hvac_state[room] = 'on'
                self.send_hvac_command(room, 'turn_on', 'heat')
        elif not is_open and self.hvac_state[room] == 'on':
            self.hvac_state[room] = 'off'
            self.send_hvac_command(room, 'turn_off')

    def send_hvac_command(self, room, command, mode=None):
        """Send HVAC command to the appropriate MQTT topic."""
        payload = json.dumps({
            "topic": self.config["published_topics"]["automatic_control"].replace('<roomID>', room),
            "message": {
                "device_id": "Temperature optimization and energy efficiency block",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "control_command": command,
                    "mode": mode
                }
            }
        })
        self.client.publish(self.config["published_topics"]["automatic_control"].replace('<roomID>', room), payload)
        print(f"[{room}] Sent HVAC command: {command}")

    def check_alerts(self, room, temperature, humidity):
        """Check for any temperature or humidity alerts."""
        alert_triggered = False

        if temperature > self.alert_temperature[room]['upper']:
            alert_message = f"ALERT: Temperature too high! Current temperature: {temperature}°C"
            self.send_alert(room, alert_message)
            alert_triggered = True
        elif temperature < self.alert_temperature[room]['lower']:
            alert_message = f"ALERT: Temperature too low! Current temperature: {temperature}°C"
            self.send_alert(room, alert_message)
            alert_triggered = True

        if humidity > self.alert_humidity[room]['upper']:
            alert_message = f"ALERT: Humidity too high! Current humidity: {humidity}%"
            self.send_alert(room, alert_message)
            alert_triggered = True
        elif humidity < self.alert_humidity[room]['lower']:
            alert_message = f"ALERT: Humidity too low! Current humidity: {humidity}%"
            self.send_alert(room, alert_message)
            alert_triggered = True

        if not alert_triggered:
            print(f"[{room}] No alerts triggered for temperature or humidity.")

    def send_alert(self, room, message):
        """Send an alert message to the appropriate MQTT topic."""
        payload = json.dumps({
            "topic": self.config["published_topics"]["alert"].replace('<roomID>', room),
            "message": {
                "device_id": "Temperature optimization and energy efficiency block",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "alert": message
                }
            }
        })
        self.client.publish(self.config["published_topics"]["alert"].replace('<roomID>', room), payload)
        print(f"[{room}] Sent alert: {message}")

    def stop(self):
        """Stop the MQTT client."""
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT client stopped and disconnected.")

def initialize_service(config_dict):
    """Initialize and register the service."""
    register_service(config_dict, service.service_catalog_url)
    print("Temperature Optimization Service Initialized and Registered")

def stop_service(signum, frame):
    """Cleanly stop the service."""
    print("Stopping service...")
    delete_service("hvac_control",service.service_catalog_url)
    service.stop()

if __name__ == "__main__":
    # Load configuration from config.json
    # with open('C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\Temperature_optimization_and_energy_efficiency\\config_temperature.json') as config_file:
    with open('config_temperature.json') as config_file:
        config = json.load(config_file)

    # Initialize the service with the loaded configuration
    service = TempOptimizationService(config)
    initialize_service(config)

    # Signal handler for clean shutdown
    signal.signal(signal.SIGINT, stop_service)

    try:
        # Start MQTT loop (no REST server here)
        service.client.loop_forever()
    finally:
        # Ensure that stop_service is called on exit
        service.stop()
