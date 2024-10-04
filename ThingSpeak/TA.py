import json
import time
import requests
from datetime import datetime
from MyMQTT import MyMQTT
from registration_functions import register_service, delete_service

# Load settings from settings.json
with open('config_thingspeak.json') as f:
    settings = json.load(f)

# MQTT Configuration
broker_ip = settings['brokerIP']
broker_port = settings['brokerPort']
thingspeak_url = settings['ThingspeakURL_write']

# MQTT topics from settings
mqtt_topics = settings['mqttTopics']

# ThingSpeak channel information
channels = settings['channels']

# Cache to store the latest values for each field
field_cache = {room: {field: None for field in channels[room]['fields']} for room in channels}

class ThingspeakAdaptor:
    def __init__(self):
        """Initialize the MQTT client and register the service."""
        # Initialize the MQTT client
        self.mqtt_client = MyMQTT(clientID="ThingspeakAdaptor", broker=broker_ip, port=broker_port, notifier=self)
        self.mqtt_client.start()

        # Subscribe to room-specific topics
        for topic in mqtt_topics.values():
            self.mqtt_client.mySubscribe(topic)

        # Subscribe to the aggregated machine availability topics
        self.subscribe_to_machine_availability()

        # Initialize the service at startup
        self.initialize_service()

    def subscribe_to_machine_availability(self):
        """Subscribe to all machine availability topics (aggregated)."""
        machine_types = ['treadmill', 'elliptical_trainer', 'stationary_bike', 'rowing_machine',
                         'cable_machine', 'leg_press_machine', 'smith_machine', 'lat_pulldown_machine']
        for machine_type in machine_types:
            self.mqtt_client.mySubscribe(f'gym/group_availability/{machine_type}')

    def notify(self, topic, payload):
        """Handle received MQTT messages."""
        payload = json.loads(payload.decode())

        # Handle environmental data for Cardio, Lifting, Changing Room, and Entrance Room
        if topic in [mqtt_topics['cardio_room'], mqtt_topics['lifting_room'], mqtt_topics['changing_room'], mqtt_topics['entrance_room']]:
            room = self.get_room_from_topic(topic)
            if room:
                try:
                    temperature = payload.get('temperature')
                    humidity = payload.get('humidity')
                    if temperature is not None:
                        self.update_cache(room, 'temperature', temperature)
                    if humidity is not None:
                        self.update_cache(room, 'humidity', humidity)
                    # Send the data for all fields in this room
                    self.upload_to_thingspeak(room)
                except (KeyError, json.JSONDecodeError) as e:
                    print(f"Error processing room data for {room}: {e}")

        # Handle current occupancy data for Entrance
        elif topic == mqtt_topics['current_occupancy']:
            try:
                current_occupancy = payload.get('current_occupancy')
                temperature = payload.get('temperature')  # Add temperature
                humidity = payload.get('humidity')        # Add humidity
                
                if current_occupancy is not None:
                    self.update_cache('Entrance', 'current_occupancy', current_occupancy)
                if temperature is not None:
                    self.update_cache('Entrance', 'temperature', temperature)
                if humidity is not None:
                    self.update_cache('Entrance', 'humidity', humidity)
                    
                # Send the data for all fields in this room
                self.upload_to_thingspeak('Entrance')
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Error processing occupancy data: {e}")

        # Handle aggregated machine availability data
        elif 'gym/group_availability/' in topic:
            try:
                machine_type = topic.split('/')[-1]  # Extract the machine type from the topic
                if 'message' in payload and 'data' in payload['message']:
                    available_machines = payload['message']['data'].get('available', None)  # Extract available machines
                    if available_machines is not None:
                        # Handle machines for Lifting Room or Cardio Room
                        if machine_type in ['cable_machine', 'leg_press_machine', 'smith_machine', 'lat_pulldown_machine']:
                            self.update_cache('Lifting Room', machine_type, available_machines)
                            self.upload_to_thingspeak('Lifting Room')
                        else:
                            self.update_cache('Cardio Room', machine_type, available_machines)
                            self.upload_to_thingspeak('Cardio Room')
                    else:
                        print(f"Warning: No available machines for {machine_type}")
                else:
                    print(f"Warning: No message or data found in payload for {machine_type}")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Error reading machine availability data: {machine_type}")

    def update_cache(self, room, field_name, value):
        """Update the cache for a specific field in a room."""
        if room in field_cache and field_name in field_cache[room]:
            field_cache[room][field_name] = value

    def upload_to_thingspeak(self, room):
        """Upload data to ThingSpeak for the specified room."""
        global field_cache
        if room in channels:
            api_key = channels[room]['writeAPIkey']
            fields = channels[room]['fields']

            # Prepare the request URL with all available fields in the cache
            update_data = {}
            for field_name, field_number in fields.items():
                if field_cache[room][field_name] is not None:
                    update_data[f'field{field_number}'] = field_cache[room][field_name]

            # Build the request URL with all fields to update
            if update_data:
                url = f"{thingspeak_url}api_key={api_key}&" + '&'.join([f'{k}={v}' for k, v in update_data.items()])
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        print(f"Uploaded data to {room}: {update_data}")
                    else:
                        print(f"Failed to upload to ThingSpeak. Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Error uploading data: {e}")
            else:
                print(f"No data to upload for {room}")

    def get_room_from_topic(self, topic):
        """Get the room name based on the topic."""
        if topic == mqtt_topics['cardio_room']:
            return 'Cardio Room'
        elif topic == mqtt_topics['lifting_room']:
            return 'Lifting Room'
        elif topic == mqtt_topics['changing_room']:
            return 'Changing Room'
        elif topic == mqtt_topics['entrance_room']:
            return 'Entrance'
        return None

    def initialize_service(self):
    # Register the service at startup
     with open('config_thingspeak_adaptor.json') as f:
        config_dict = json.load(f)
     register_service(config_dict)
     print("Thingspeak Adaptor Service Initialized and Registered")

    def stop(self):
        """Stop the MQTT client and unregister the service."""
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
