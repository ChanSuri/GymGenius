import json
import time
import requests
import signal
from MyMQTT import MyMQTT
from registration_functions import register_service, delete_service

class ThingspeakAdaptor:
    def __init__(self):
        """Initialize the Thingspeak Adaptor and fetch configuration from both the service catalog and the ThingSpeak config."""
        # Load the service catalog URL from config_thingspeak_adaptor.json
        self.config_adaptor = self.load_adaptor_config()
        self.service_catalog_url = self.config_adaptor['service_catalog']

        # Retrieve the full service catalog
        self.config_dict = self.get_service_catalog()
        self.broker_ip = self.config_dict['brokerIP']
        self.broker_port = self.config_dict['brokerPort']
        self.rooms = self.config_dict['roomsID']
        self.machines = self.config_dict['machinesID']

        # Load ThingSpeak configuration from the separate config file
        self.thingspeak_config = self.load_thingspeak_config()
        self.thingspeak_url = self.thingspeak_config['ThingspeakURL_write']
        self.channels = self.thingspeak_config['channels']

        # Initialize field_cache to store the latest values for each room and field
        self.field_cache = {room: {field: None for field in self.channels[room]['fields']} for room in self.channels}

        # Get service details
        self.occupancy_service = self.config_dict['services']['occupancy']
        self.hvac_service = self.config_dict['services']['hvac_control']
        self.device_connector_service = self.config_dict['services']['device_connector']
        self.machine_availability_service = self.config_dict['services']['machine_availability']

        # Initialize MQTT client
        self.mqtt_client = MyMQTT(clientID="ThingspeakAdaptor", broker=self.broker_ip, port=self.broker_port, notifier=self)
        self.mqtt_client.start()

        # Subscribe to the topics dynamically based on the services
        self.subscribe_to_services()

    def load_adaptor_config(self):
        """Load the configuration for the adaptor from config_thingspeak_adaptor.json."""
        try:
            with open('config_thingspeak_adaptor.json') as f:
                return json.load(f)
        except FileNotFoundError as e:
            print(f"Error loading adaptor configuration: {e}")
            return {}

    def get_service_catalog(self):
        """Retrieve the service catalog data."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                return response.json()  # Return the full catalog as a dictionary
            else:
                raise Exception(f"Failed to retrieve service catalog: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving service catalog: {e}")
            return {}

    def load_thingspeak_config(self):
        """Load the ThingSpeak configuration from a local JSON file."""
        try:
            with open('config_thingspeak.json') as f:
                return json.load(f)
        except FileNotFoundError as e:
            print(f"Error loading ThingSpeak configuration: {e}")
            return {}

    def subscribe_to_services(self):
        """Subscribe to the necessary MQTT topics based on the services defined in the catalog."""
        # Subscribe to the current occupancy topic
        self.mqtt_client.mySubscribe(self.occupancy_service['published_topics']['current_occupancy'])  # gym/occupancy/current

        # Subscribe to environment (temperature, humidity) topics for each room from device_connector
        for room in self.rooms:
            room_topic = self.device_connector_service['published_topics']['enviroment'].replace('<roomID>', room)
            self.mqtt_client.mySubscribe(room_topic)  # gym/environment/<roomID>

        # Subscribe to machine availability topic
        self.mqtt_client.mySubscribe(self.machine_availability_service['published_topics']['group_availability_x_machine_type'])  # gym/group_availability/#

    def notify(self, topic, payload):
        """Handle received MQTT messages and process them accordingly."""
        payload = json.loads(payload.decode())
        if topic == self.occupancy_service['published_topics']['current_occupancy']:
            self.handle_occupancy_data(payload)
        elif 'environment' in topic:
            self.handle_environment_data(topic, payload)
        elif 'group_availability' in topic:
            self.handle_machine_availability(topic, payload)

    def handle_occupancy_data(self, payload):
        """Handle occupancy data (current occupancy)."""
        current_occupancy = payload.get('current_occupancy')
        if current_occupancy is not None:
            self.update_cache('Entrance', 'current_occupancy', current_occupancy)
            self.upload_to_thingspeak('Entrance')

    def handle_environment_data(self, topic, payload):
        """Handle environment data (temperature, humidity)."""
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
        available_machines = payload.get('available', None)
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
        """Get the room name based on the topic."""
        for room in self.rooms:
            if room in topic:
                return room
        return None

    def stop(self):
        """Stop the MQTT client."""
        self.mqtt_client.stop()
        print("MQTT client stopped.")

# Functions outside the class for service registration and stopping

def initialize_service(adaptor):
    """Register the service at startup."""
    register_service(adaptor.config_dict, adaptor.service_catalog_url)
    print("Thingspeak Adaptor Service Initialized and Registered")

def stop_service(signum, frame):
    """Unregister and stop the service."""
    print("Stopping service...")
    delete_service("thingspeak_adaptor", adaptor.service_catalog_url)
    adaptor.stop()

if __name__ == "__main__":
    # Initialize the service and register it
    adaptor = ThingspeakAdaptor()
    initialize_service(adaptor)

    # Set up signal handling to allow clean shutdown
    signal.signal(signal.SIGINT, stop_service)

    try:
        # Main loop to keep the service running and receiving MQTT messages
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        # Handle service stop on manual interruption
        stop_service(None, None)
