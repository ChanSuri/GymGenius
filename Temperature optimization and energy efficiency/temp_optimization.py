import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timedelta
import signal
from registration_functions import *

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_env_base = "gym/environment/"
mqtt_topic_control_base = "gym/hvac/control/"
mqtt_topic_desired_temperature_base = "gym/desired_temperature/"
mqtt_topic_occupancy = "gym/occupancy/current"
mqtt_topic_HVAC_on_off_base = "gym/hvac/on_off/"
mqtt_topic_alert_base = "gym/environment/alert/"

rooms = ["entrance", "cardio_room", "lifting_room", "changing_room"]

class TempOptimizationService:

    def __init__(self, gym_schedule):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        # Subscribe to topics for all rooms
        self.client.subscribe(mqtt_topic_env_base + '#')
        self.client.subscribe(mqtt_topic_desired_temperature_base + '#')
        self.client.subscribe(mqtt_topic_HVAC_on_off_base + '#')

        self.client.subscribe(mqtt_topic_occupancy)

        self.gym_schedule = gym_schedule
        self.thresholds = {room: {'upper': 28, 'lower': 24} for room in rooms}  # Default thresholds for each room
        self.alert_temperature = {'upper': 35, 'lower': 15}
        self.alert_humidity = {room: {'upper': 70, 'lower': 20} for room in rooms} # Humidity alert thresholds for each room
        self.alert_humidity['changing_room']['lower'] = 0
        self.alert_humidity['changing_room']['upper'] = 100
        self.hvac_state = {room: 'off' for room in rooms}
        self.current_occupancy = 0
        self.current_command = {room: "ON" for room in rooms}  # Default command state is ON for each room

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
        # Determine the room from the topic
        for room in rooms:
            if message.topic.startswith(mqtt_topic_env_base + room):
                self.handle_environment_data(room, message)
            elif message.topic.startswith(mqtt_topic_desired_temperature_base + room):
                self.handle_desired_temperature(room, message)
            elif message.topic.startswith(mqtt_topic_HVAC_on_off_base + room):
                self.handle_hvac_on_off(room, message)

        if message.topic == mqtt_topic_occupancy:
            self.handle_occupancy(message)

    def handle_environment_data(self, room, message):
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
        try:
            command_data = json.loads(message.payload.decode())
            self.current_command[room] = command_data['message']['data'].get('state', "ON").upper()
            print(f"[{room}] Received administrator command: {self.current_command[room]}.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to decode command data for {room}: {e}")

    def handle_occupancy(self, message):
        try:
            occupancy_data = json.loads(message.payload.decode())
            self.current_occupancy = occupancy_data['message']['data'].get('current_occupancy', 0)
            print(f"Received occupancy data: {self.current_occupancy} clients present.")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to decode occupancy data: {e}")

    def control_hvac(self, room, temperature, humidity):
        # If the command is OFF or ON, do not proceed with controlling the HVAC
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
        payload = json.dumps({
            "topic": mqtt_topic_control_base + room,
            "message": {
                "device_id": "Temperature optimization and energy efficiency block",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "control_command": command,
                    "mode": mode
                }
            }
        })
        self.client.publish(mqtt_topic_control_base + room, payload)
        print(f"[{room}] Sent HVAC command: {command}")

    def check_alerts(self, room, temperature, humidity):
        alert_triggered = False

        if temperature > self.alert_temperature['upper']:
            alert_message = f"ALERT: Temperature too high! Current temperature: {temperature}°C"
            self.send_alert(room, alert_message)
            alert_triggered = True
        elif temperature < self.alert_temperature['lower']:
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
        # Publish the alert in the required JSON structure
        payload = json.dumps({
            "topic": mqtt_topic_alert_base + room,
            "message": {
                "device_id": "Temperature optimization and energy efficiency block",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "alert": message
                }
            }
        })
        self.client.publish(mqtt_topic_alert_base + room, payload)
        print(f"[{room}] Sent alert: {message}")

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
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
