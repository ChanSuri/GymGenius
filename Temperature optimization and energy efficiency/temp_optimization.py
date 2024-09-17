import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timedelta
import signal
from registration_functions import *

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_env = "gym/environment"
mqtt_topic_control = "gym/hvac/control"
mqtt_topic_desired_temperature = "gym/desired_temperature"  # Topic for desired temperature update
mqtt_topic_occupancy = "gym/occupancy/current"  # Topic for current occupancy
mqtt_topic_HVAC_on_off = "gym/hvac/on_off"  # Topic for administrator control (ON/OFF)
mqtt_topic_alert = "gym/environment/alert"  # Topic for publishing alerts

class TempOptimizationService:

    def __init__(self, gym_schedule):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        self.client.subscribe(mqtt_topic_env)
        self.client.subscribe(mqtt_topic_desired_temperature)  # Subscribing to desired temperature topic
        self.client.subscribe(mqtt_topic_occupancy)  # Subscribing to occupancy topic
        self.client.subscribe(mqtt_topic_HVAC_on_off)  # Subscribing to HVAC on/off control topic

        self.gym_schedule = gym_schedule
        self.thresholds = {'upper': 28, 'lower': 24}  # Default thresholds
        self.alert_temperature = {'upper': 35, 'lower': 15}  # Alert thresholds for temperature
        self.alert_humidity = {'upper': 70, 'lower': 20}  # Alert thresholds for humidity
        self.hvac_state = 'off'
        self.current_occupancy = 0  # Initialize the occupancy to 0
        self.current_command = "ON"  # Default command state is ON

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
                    print(f"Received temperature: {temperature}°C, humidity: {humidity}%")
                    self.control_hvac(temperature, humidity)
                    self.check_alerts(temperature, humidity)  # Check for temperature and humidity alerts
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to decode environment data: {e}")
        
        elif message.topic == mqtt_topic_desired_temperature:  # Handle threshold updates via MQTT
            try:
                threshold_data = json.loads(message.payload.decode())
                desired_temperature = threshold_data['message']['data'].get('desired_temperature')
                upper = desired_temperature + 1
                lower = desired_temperature - 1

                # Validate and set the thresholds with bounds
                if upper is not None and isinstance(upper, (int, float)):
                    self.thresholds['upper'] = max(15, min(upper, 35))  # Limit thresholds to realistic values
                if lower is not None and isinstance(lower, (int, float)):
                    self.thresholds['lower'] = max(15, min(lower, 35))

                print(f"Updated desired temperature and thresholds: temperature = {desired_temperature}°C, upper = {self.thresholds['upper']}°C, lower = {self.thresholds['lower']}°C")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to decode threshold data: {e}")

        elif message.topic == mqtt_topic_occupancy:  # Handle occupancy updates via MQTT
            try:
                occupancy_data = json.loads(message.payload.decode())
                self.current_occupancy = occupancy_data['message']['data'].get('current_occupancy', 0)
                print(f"Received occupancy data: {self.current_occupancy} clients present.")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to decode occupancy data: {e}")

        elif message.topic == mqtt_topic_HVAC_on_off:  # Handle HVAC controls command
            try:
                command_data = json.loads(message.payload.decode())
                self.current_command = command_data['message']['data'].get('state', "ON").upper()  # Retrieve from the "state" field, default to "ON"
                print(f"Received administrator command: {self.current_command}.")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Failed to decode command data: {e}")

    def control_hvac(self, temperature, humidity):
        # If the command is OFF, do not proceed with controlling the HVAC
        if self.current_command == "OFF":
            print("HVAC control disabled by administrator.")
            return

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
        if is_open and self.hvac_state == 'off':
            if temperature > self.thresholds['upper']:
                self.hvac_state = 'on'
                self.send_hvac_command('turn_on','cool')
            elif temperature < self.thresholds['lower']:
                self.hvac_state = 'on'
                self.send_hvac_command('turn_on','heat')
        elif not is_open and self.hvac_state == 'on':
            self.hvac_state = 'off'
            self.send_hvac_command('turn_off')

    def send_hvac_command(self, command, mode = None):
        # Publish the command in the required JSON structure
        payload = json.dumps({
            "topic": mqtt_topic_control,
            "message": {
                "device_id": "Temperature optimization and energy efficiency block",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "control_command": command,
                    "mode": mode
                }
            }
        })
        self.client.publish(mqtt_topic_control, payload)
        print(f"Sent HVAC command: {command}")

    # Function to check if the temperature or humidity exceeds alert thresholds
    def check_alerts(self, temperature, humidity):
        alert_triggered = False

        # Check temperature alerts
        if temperature > self.alert_temperature['upper']:
            alert_message = f"ALERT: Temperature too high! Current temperature: {temperature}°C"
            self.send_alert(alert_message)
            alert_triggered = True
        elif temperature < self.alert_temperature['lower']:
            alert_message = f"ALERT: Temperature too low! Current temperature: {temperature}°C"
            self.send_alert(alert_message)
            alert_triggered = True

        # Check humidity alerts
        if humidity > self.alert_humidity['upper']:
            alert_message = f"ALERT: Humidity too high! Current humidity: {humidity}%"
            self.send_alert(alert_message)
            alert_triggered = True
        elif humidity < self.alert_humidity['lower']:
            alert_message = f"ALERT: Humidity too low! Current humidity: {humidity}%"
            self.send_alert(alert_message)
            alert_triggered = True

        if not alert_triggered:
            print("No alerts triggered for temperature or humidity.")

    # Function to publish an alert message to the MQTT topic
    def send_alert(self, message):
        # Publish the alert in the required JSON structure
        payload = json.dumps({
            "topic": mqtt_topic_alert,
            "message": {
                "device_id": "Temperature optimization and energy efficiency block",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "alert": message
                }
            }
        })
        self.client.publish(mqtt_topic_alert, payload)
        print(f"Sent alert: {message}")

    def stop(self):
        self.client.loop_stop()  # Stop the MQTT loop
        self.client.disconnect()  # Cleanly disconnect from the broker
        print("MQTT client stopped and disconnected.")

def initialize_service():
    # Register the service at startup
    service_id = "hvac_control"
    description = "HVAC management and control"
    status = "active"
    endpoint = "http://localhost:8084/hvac"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    register_service(service_id, description, status, endpoint, timestamp)
    print("Temperature Optimization Service Initialized and Registered")

def stop_service(signum, frame):
    print("Stopping service...")
    delete_service("hvac_control")
    # Clean stop of the MQTT client
    service.stop()


if __name__ == "__main__":
    gym_schedule = {'open': datetime.strptime('08:00', '%H:%M').time(),
                    'close': datetime.strptime('24:00', '%H:%M').time()}

    # Initialize the service
    service = TempOptimizationService(gym_schedule)
    initialize_service()

    # Signal handler for clean shutdown
    signal.signal(signal.SIGINT, stop_service)

    try:
        # Start MQTT loop (no REST server here)
        service.client.loop_forever()
    finally:
        # Ensure that stop_service is called on exit
        service.stop()