import json
import time
import requests
import signal
import paho.mqtt.client as mqtt
from registration_functions import *

class ThingspeakAdaptor:
    def __init__(self, config):
        self.config = config
        self.service_catalog_url = config['service_catalog']

        # Get MQTT broker, port, roomsID, and machinesID from the service catalog
        self.mqtt_broker, self.mqtt_port, self.roomsID, self.machinesID = self.get_info_from_service_catalog()

        # Load ThingSpeak configuration from config_thingspeak.json
        self.thingspeak_config = self.load_thingspeak_config()
        self.thingspeak_url = self.thingspeak_config['ThingspeakURL_write']
        self.channels = self.thingspeak_config['channels']

        # Initialize MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        # Field cache to store the latest values for each room and field
        self.field_cache = {room: {field: None for field in self.channels[room]['fields']} for room in self.channels}

    def get_info_from_service_catalog(self):
        """Retrieve MQTT broker, port, roomsID, and machinesID from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                catalog = response.json().get('catalog', {})
                return catalog.get('brokerIP'), catalog.get('brokerPort'), catalog.get('roomsID'), catalog.get('machinesID')
            else:
                raise Exception(f"Failed to retrieve service catalog: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving info from service catalog: {e}")
            return None, None, [], []

    def load_thingspeak_config(self):
        """Load the ThingSpeak configuration from a local JSON file."""
        try:
            with open('config_thingspeak.json') as f:
                return json.load(f)
        except FileNotFoundError as e:
            print(f"Error loading ThingSpeak configuration: {e}")
            return {}

    def connect_mqtt(self):
        """Connect to the MQTT broker."""
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
        """Callback when the client connects to the MQTT broker."""
        if rc == 0:
            print("Connected to MQTT broker.")
            self.subscribe_to_topics()
        else:
            print(f"Failed to connect to MQTT broker. Return code: {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback when the client disconnects from the MQTT broker."""
        print(f"Disconnected from MQTT broker with return code {rc}. Reconnecting...")
        self.connect_mqtt()

    def subscribe_to_topics(self):
        """Subscribe to MQTT topics dynamically based on roomsID and machinesID."""
        try:
            # Subscribe to environment topics for each room
            env_topic_template = self.config['subscribed_topics'].get('enviroments')
            if env_topic_template:
                for room in self.roomsID:
                    topic = env_topic_template.replace('<roomID>', room)
                    self.client.subscribe(topic)
                    print(f"Subscribed to environment topic: {topic}")

            # Subscribe to machine availability topics for each machine
            machine_topic_template = self.config['subscribed_topics'].get('machine_availability')
            if machine_topic_template:
                for machine in self.machinesID:
                    machine_type = '_'.join(machine.split('_')[:-1])  # Extract machine type from machine name
                    topic = machine_topic_template.replace('<machine_type>', machine_type)
                    self.client.subscribe(topic)
                    print(f"Subscribed to machine availability topic: {topic}")

            # Subscribe to occupancy topic
            occupancy_topic = self.config['subscribed_topics'].get('current_occupancy')
            if occupancy_topic:
                self.client.subscribe(occupancy_topic)
                print(f"Subscribed to occupancy topic: {occupancy_topic}")

        except KeyError as e:
            print(f"Error subscribing to topics: {e}")

    def on_message(self, client, userdata, msg):
        """Callback for handling received MQTT messages."""
        try:
            payload = json.loads(msg.payload.decode())  # Convert the payload from JSON to a Python object
            topic = msg.topic  # Get the topic from the message

            # Identify the topic and process the data
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
        try:
            occupancy_data = payload['message']['data']
            current_occupancy = occupancy_data.get('current_occupancy')
            if current_occupancy is not None:
                self.update_cache('entrance', 'current_occupancy', current_occupancy)
                self.upload_to_thingspeak('entrance')
        except KeyError as e:
            print(f"Error handling occupancy data: {e}")

    def handle_environment_data(self, topic, payload):
        """Handle environment data like temperature and humidity."""
        try:
            room = self.get_room_from_topic(topic)
            if room:
                data_points = payload['e']  # List of environment data (temperature, humidity)
                temperature = None
                humidity = None
                for data_point in data_points:
                    if data_point['n'] == 'temperature':
                        temperature = data_point['v']
                    elif data_point['n'] == 'humidity':
                        humidity = data_point['v']
                
                if temperature is not None:
                    self.update_cache(room, 'temperature', temperature)
                if humidity is not None:
                    self.update_cache(room, 'humidity', humidity)
                self.upload_to_thingspeak(room)
        except KeyError as e:
            print(f"Error handling environment data: {e}")

    def handle_machine_availability(self, topic, payload):
        """Handle machine availability data."""
        try:
            machine_type = topic.split('/')[-1]  # Extract the machine type from the topic
            availability_data = payload['message']['data']  # Extract the data from the payload
            available_machines = availability_data.get('available')
            if available_machines is not None:
                room = 'lifting_room' if machine_type in ['cable_machine', 'leg_press_machine', 'smith_machine', 'lat_pulldown_machine'] else 'cardio_room'
                self.update_cache(room, machine_type, available_machines)
                self.upload_to_thingspeak(room)
        except KeyError as e:
            print(f"Error handling machine availability data: {e}")

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
        """Extract room name from the topic."""
        for room in self.roomsID:
            if room in topic:
                return room
        return None

    def stop(self):
        """Stop the MQTT client."""
        self.client.loop_stop()
        self.client.disconnect()
        print("MQTT client stopped.")

# Service initialization and signal handling

def initialize_service(config_dict):
    """Register the service at startup."""
    register_service(config_dict, config_dict['service_catalog'])
    print("Thingspeak Adaptor Service Initialized and Registered")

def stop_service(signum, frame):
    """Unregister and stop the service."""
    with open('config_thingspeak_adaptor.json') as config_file:
        config_dict = json.load(config_file)
    print("Stopping service...")
    delete_service("thingspeak_adaptor", config_dict['service_catalog'])
    
    adaptor.stop()

if __name__ == "__main__":
    # Load configuration from config_thingspeak_adaptor.json
    with open('config_thingspeak_adaptor.json') as config_file:
        config_dict = json.load(config_file)

    # Initialize the service with the loaded configuration
    initialize_service(config_dict)

    # Signal handler for clean stop
    signal.signal(signal.SIGINT, stop_service)

    adaptor = ThingspeakAdaptor(config_dict)

    # Start the MQTT client loop
    adaptor.client.loop_start()

    # Keep the service running
    while True:
        time.sleep(60)
