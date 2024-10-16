import json
import time
import requests
import signal
import paho.mqtt.client as mqtt
from registration_functions import register_service, delete_service

class ThingspeakAdaptor:
    def __init__(self, config):
        self.config = config
        self.service_catalog_url = config['service_catalog']

        # Get MQTT broker and port from service catalog
        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()
        
        # Load ThingSpeak configuration from config file
        self.thingspeak_config = self.load_thingspeak_config()
        self.thingspeak_url = self.thingspeak_config['ThingspeakURL_write']
        self.channels = self.thingspeak_config['channels']

        # Initialize MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        # Field cache to store latest values for each room and field
        self.field_cache = {room: {field: None for field in self.channels[room]['fields']} for room in self.channels}

    def get_mqtt_info_from_service_catalog(self):
        """Retrieve MQTT broker and port information from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                catalog = response.json().get('catalog', {})
                return catalog.get('brokerIP'), catalog.get('brokerPort')
            else:
                raise Exception(f"Failed to get broker information: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting MQTT info from service catalog: {e}")
            return None, None

    def load_thingspeak_config(self):
        """Load the ThingSpeak configuration from a local JSON file."""
        try:
            with open('config_thingspeak.json') as f:
                return json.load(f)
        except FileNotFoundError as e:
            print(f"Error loading ThingSpeak configuration: {e}")
            return {}

    def connect_mqtt(self):
        try:
            if self.mqtt_broker:
                self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
                print("MQTT connected successfully.")
            else:
                print("No MQTT broker information found.")
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            time.sleep(5)
            self.connect_mqtt()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker.")
            self.subscribe_to_topics()
        else:
            print(f"Failed to connect to MQTT broker. Return code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with return code {rc}. Reconnecting...")
        self.connect_mqtt()

    def subscribe_to_topics(self):
        """Subscribe to topics defined in the service catalog."""
        # Subscribing to necessary topics from service catalog
        try:
            for room in self.channels:
                for field_name in self.channels[room]['fields']:
                    topic = self.config['subscribed_topics'].get(field_name)
                    if topic:
                        self.client.subscribe(topic)
                        print(f"Subscribed to topic: {topic}")
        except KeyError as e:
            print(f"Error subscribing to topics: {e}")

    def on_message(self, client, userdata, msg):
        """Callback for handling received MQTT messages."""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic

            # Handle message based on the topic
            if topic == self.config['subscribed_topics'].get('current_occupancy'):
                self.handle_occupancy_data(payload)
            elif 'environment' in topic:
                self.handle_environment_data(topic, payload)
            elif 'group_availability' in topic:
                self.handle_machine_availability(topic, payload)
        except json.JSONDecodeError as e:
            print(f"Error decoding message: {e}")

    def handle_occupancy_data(self, payload):
        """Handle occupancy data."""
        current_occupancy = payload.get('current_occupancy')
        if current_occupancy is not None:
            self.update_cache('Entrance', 'current_occupancy', current_occupancy)
            self.upload_to_thingspeak('Entrance')

    def handle_environment_data(self, topic, payload):
        """Handle environment data."""
        room = self.get_room_from_topic(topic)
        if room:
            temperature = payload.get('temperature')
            humidity = payload.get('humidity')
            if temperature is not None:
                self.update_cache(room, 'temperature', temperature)
            if humidity is not None:
                self.update_cache(room, 'humidity', humidity)
            self.upload_to_thingspeak(room)

    def handle_machine_availability(self, topic, payload):
        """Handle machine availability data."""
        machine_type = topic.split('/')[-1]
        available_machines = payload.get('available')
        if available_machines is not None:
            room = 'Lifting Room' if machine_type in ['cable_machine', 'leg_press_machine', 'smith_machine', 'lat_pulldown_machine'] else 'Cardio Room'
            self.update_cache(room, machine_type, available_machines)
            self.upload_to_thingspeak(room)

    def update_cache(self, room, field_name, value):
        """Update the cache for a specific field in a room."""
        if room in self.field_cache and field_name in self.field_cache[room]:
            self.field_cache[room][field_name] = value

    def upload_to_thingspeak(self, room):
        """Upload data to ThingSpeak for the specified room."""
        if room in self.channels:
            api_key = self.channels[room]['writeAPIkey']
            fields = self.channels[room]['fields']

            # Prepare the request URL with all available fields in the cache
            update_data = {}
            for field_name, field_number in fields.items():
                if self.field_cache[room][field_name] is not None:
                    update_data[f'field{field_number}'] = self.field_cache[room][field_name]

            if update_data:
                url = f"{self.thingspeak_url}api_key={api_key}&" + '&'.join([f'{k}={v}' for k, v in update_data.items()])
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
        """Extract room name from topic."""
        for room in self.channels:
            if room in topic:
                return room
        return None

    def stop(self):
        """Stop the MQTT client."""
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT client stopped.")

# Service initialization and signal handling

def initialize_service(adaptor):
    """Register the service at startup."""
    register_service(adaptor.config, adaptor.service_catalog_url)
    print("Thingspeak Adaptor Service Initialized and Registered")

def stop_service(signum, frame):
    """Unregister and stop the service."""
    print("Stopping service...")
    delete_service("thingspeak_adaptor", adaptor.service_catalog_url)
    adaptor.stop()

if __name__ == "__main__":
    # Load configuration from config.json
    with open('config_thingspeak_adaptor.json') as config_file:
        config = json.load(config_file)

    # Initialize the service with the loaded configuration
    adaptor = ThingspeakAdaptor(config)
    initialize_service(adaptor)

    # Signal handler for clean stop
    signal.signal(signal.SIGINT, stop_service)

    # Start the MQTT client loop
    adaptor.client.loop_start()

    # Keep the service running
    while True:
        time.sleep(60)
