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

        # Retrieve broker and port information
        self.broker_ip, self.broker_port = self.get_broker_info()
        
        # Retrieve room and machine information
        self.rooms, self.machines = self.get_room_and_machine_info()

        # Check if the critical information is available
        if not self.broker_ip or not self.broker_port:
            raise ValueError("brokerIP or brokerPort missing in service catalog")

        # Load ThingSpeak configuration from the separate config file
        self.thingspeak_config = self.load_thingspeak_config()
        self.thingspeak_url = self.thingspeak_config['ThingspeakURL_write']
        self.channels = self.thingspeak_config['channels']

        # Initialize field_cache to store the latest values for each room and field
        self.field_cache = {room: {field: None for field in self.channels[room]['fields']} for room in self.channels}

        # Retrieve services (occupancy, hvac, device_connector, machine_availability)
        self.occupancy_service, self.hvac_service, self.device_connector_service, self.machine_availability_service = self.get_services()

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

    def get_broker_info(self):
        """Retrieve broker information from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                catalog = response.json().get('catalog', {})
                return catalog.get('brokerIP'), catalog.get('brokerPort')
            else:
                raise Exception(f"Failed to retrieve broker info: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving broker info: {e}")
            return None, None

    def get_room_and_machine_info(self):
        """Retrieve room and machine information from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                catalog = response.json().get('catalog', {})
                return catalog.get('roomsID', []), catalog.get('machinesID', [])
            else:
                raise Exception(f"Failed to retrieve room and machine info: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving room and machine info: {e}")
            return [], []

    def get_services(self):
        """Retrieve services from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                catalog = response.json().get('catalog', {})
                services = catalog.get('services', [])
                
                occupancy_service = next((s for s in services if s['service_id'] == 'occupancy'), None)
                hvac_service = next((s for s in services if s['service_id'] == 'hvac_control'), None)
                device_connector_service = next((s for s in services if s['service_id'] == 'device_connector'), None)
                machine_availability_service = next((s for s in services if s['service_id'] == 'machine_availability'), None)

                return occupancy_service, hvac_service, device_connector_service, machine_availability_service
            else:
                raise Exception(f"Failed to retrieve services: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving services: {e}")
            return None, None, None, None

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
        if self.occupancy_service and 'published_topics' in self.occupancy_service:
            try:
                occupancy_topic = self.occupancy_service['published_topics'].get('current_occupancy')
                if occupancy_topic:
                    self.mqtt_client.mySubscribe(occupancy_topic)
                    print(f"Subscribed to occupancy topic: {occupancy_topic}")
                else:
                    print("No current_occupancy topic found in occupancy_service.")
            except Exception as e:
                print(f"Error subscribing to occupancy topic: {e}")
        
        # Subscribe to environment (temperature, humidity) topics for each room from device_connector
        if self.device_connector_service and 'published_topics' in self.device_connector_service:
            try:
                environment_topic_template = self.device_connector_service['published_topics'].get('enviroment')
                if environment_topic_template:
                    for room in self.rooms:
                        room_topic = environment_topic_template.replace('<roomID>', room)
                        self.mqtt_client.mySubscribe(room_topic)
                        print(f"Subscribed to environment topic for room {room}: {room_topic}")
                else:
                    print("No environment topic template found in device_connector_service.")
            except Exception as e:
                print(f"Error subscribing to environment topics: {e}")
        
        # Subscribe to machine availability topic
        if self.machine_availability_service and 'published_topics' in self.machine_availability_service:
            try:
                machine_availability_topic = self.machine_availability_service['published_topics'].get('group_availability_x_machine_type')
                if machine_availability_topic:
                    self.mqtt_client.mySubscribe(machine_availability_topic)
                    print(f"Subscribed to machine availability topic: {machine_availability_topic}")
                else:
                    print("No group_availability_x_machine_type topic found in machine_availability_service.")
            except Exception as e:
                print(f"Error subscribing to machine availability topic: {e}")

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
