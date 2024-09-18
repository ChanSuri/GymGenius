import json
import time
import requests
from datetime import datetime, timedelta
from MyMQTT import MyMQTT  # Import MyMQTT class for MQTT handling
from registration_functions import register_service, delete_service  # Import register_service and delete_service

# Load settings from settings.json
with open('settings.json') as f:
    settings = json.load(f)

# MQTT Configuration
broker_ip = settings['brokerIP']
broker_port = settings['brokerPort']
thingspeak_url = settings['ThingspeakURL']

# MQTT topics from settings
mqtt_topics = settings['mqttTopics']

# ThingSpeak channel information
channels = settings['channels']

# Time tracking for rate limiting (last time each channel was updated)
last_update_time = {room: datetime.min for room in channels}

class ThingspeakAdaptor:
    def __init__(self):
        # Initialize the MQTT client
        self.mqtt_client = MyMQTT(clientID="ThingspeakAdaptor", broker=broker_ip, port=broker_port, notifier=self)
        self.mqtt_client.start()

        # Subscribe to room-specific topics
        self.mqtt_client.mySubscribe(mqtt_topics['cardio_room'])
        self.mqtt_client.mySubscribe(mqtt_topics['lifting_room'])
        self.mqtt_client.mySubscribe(mqtt_topics['changing_room'])

        # Subscribe to the current occupancy topic
        self.mqtt_client.mySubscribe(mqtt_topics['current_occupancy'])

        # Subscribe to the aggregated machine availability topics
        self.subscribe_to_machine_availability()

        # Initialize the service at startup
        self.initialize_service()

    def subscribe_to_machine_availability(self):
        """Subscribe to all machine availability topics (aggregated)."""
        for machine_type in ['treadmill', 'elliptical_trainer', 'stationary_bike', 'rowing_machine', 'cable_machine', 'leg_press_machine', 'smith_machine', 'lat_pulldown_machine']:
            self.mqtt_client.mySubscribe(f'gym/group_availability/{machine_type}')

    def notify(self, topic, payload):
        """Handle received MQTT messages."""
        payload = json.loads(payload.decode())

        # Handle temperature and humidity data for Cardio and Lifting Room
        if topic == mqtt_topics['cardio_room'] or topic == mqtt_topics['lifting_room']:
            try:
                temperature = payload.get('temperature')
                humidity = payload.get('humidity')
                if temperature is not None:
                    self.upload_to_thingspeak('Cardio Room', 'temperature', temperature)
                if humidity is not None:
                    self.upload_to_thingspeak('Cardio Room', 'humidity', humidity)
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Error reading temperature or humidity: {e}")

        # Handle current occupancy data
        elif topic == mqtt_topics['current_occupancy']:
            try:
                current_occupancy = payload['message']['data']['current_occupancy']  # Extract current occupancy
                self.upload_to_thingspeak('Entrance', 'current_occupancy', current_occupancy)
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Error reading current occupancy data: {e}")

        # Handle aggregated machine availability data
        elif 'gym/group_availability/' in topic:
            try:
                machine_type = topic.split('/')[-1]  # Extract the machine type from the topic
                available_machines = payload['message']['data']['available']  # Extract the number of available machines
                self.upload_to_thingspeak('Cardio Room', machine_type, available_machines)  # Send to ThingSpeak
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Error reading machine availability data: {e}")

    def upload_to_thingspeak(self, room, field_name, value):
        """Upload data to ThingSpeak for the specified room and field."""
        global last_update_time

        # Ensure that at least 30 seconds have passed since the last update
        if datetime.now() - last_update_time[room] < timedelta(seconds=30):
            print(f"Skipping update for {room}, waiting for rate limit (30 seconds).")
            return

        if room in channels:
            api_key = channels[room]['writeAPIkey']
            field_number = channels[room]['fields'].get(field_name)

            if field_number:
                url = f"{thingspeak_url}api_key={api_key}&field{field_number}={value}"
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        print(f"Uploaded {field_name} = {value} to {room} (field {field_number})")
                        last_update_time[room] = datetime.now()
                    else:
                        print(f"Failed to upload to ThingSpeak. Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Error uploading data: {e}")
            else:
                print(f"No field number for {field_name} in {room}")

    def initialize_service(self):
        """Register the service at startup."""
        service_id = "thingspeak_adaptor"
        description = "Manages data uploads to ThingSpeak"
        status = "active"
        endpoint = "http://localhost:8080/thingspeak_adaptor"  # Example of the service endpoint
        register_service(service_id, description, status, endpoint)
        print("Thingspeak Adaptor Service Initialized and Registered with endpoint:", endpoint)

    def stop(self):
        """Stop the MQTT client and delete the service."""
        self.mqtt_client.stop()
        delete_service("thingspeak_adaptor")
        print("Thingspeak Adaptor stopped and service deleted.")

if __name__ == "__main__":
    adaptor = ThingspeakAdaptor()
    try:
        while True:
            # Let the service receive MQTT messages and update ThingSpeak
            time.sleep(60)
    except KeyboardInterrupt:
        adaptor.stop()
        print("Thingspeak Adaptor stopped.")
