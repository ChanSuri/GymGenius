import paho.mqtt.client as mqtt
import json
import time
import requests
from datetime import datetime
import signal
from registration_functions import *

# MQTT Configuration
class MachineAvailabilityService:
    def __init__(self, config):
        self.config = config
        self.service_catalog_url = config['service_catalog']  # Get service catalog URL from config.json
        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()  # Retrieve broker and port
        self.machine_types = self.get_machine_types_from_service_catalog()
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        # Initial machine status for all machine types
        self.machines = {
            machine_type: {"total": total, "available": total, "occupied": 0}
            for machine_type, total in self.machine_types.items()
        }

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

    def get_machine_types_from_service_catalog(self):
        """Retrieve machine types and their counts from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                machines_list = catalog.get('machinesID')
                machine_types = {}
                
                # Count number of machines for each type
                for machine in machines_list:
                    machine_type = '_'.join(machine.split('_')[:-1])
                    if machine_type in machine_types:
                        machine_types[machine_type] += 1
                    else:
                        machine_types[machine_type] = 1
                
                return machine_types
            else:
                raise Exception(f"Failed to get machine types: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting machine types from service catalog: {e}")
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
            self.subscribe_to_topics()  # Subscribe to all machine availability topics
        else:
            print(f"Failed to connect to MQTT broker. Return code: {rc}")

    def subscribe_to_topics(self):
        """Subscribe to topics listed in the config file."""
        try:
            for topic_key, topic_value in self.config["subscribed_topics"].items():
                self.client.subscribe(topic_value)
                print(f"Subscribed to topic: {topic_value}")
        except KeyError as e:
            print(f"Error in subscribed_topics format: {e}")

    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with return code {rc}. Reconnecting...")
        self.connect_mqtt()

    def on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            availability = payload['e']['v']  # Extract availability status (0 = available, 1 = occupied)
            machine_topic = payload['bn']  # Extract machine base name from 'bn'

            # Extract machine type from topic, e.g., "gym/availability/treadmill/1"
            topic_parts = machine_topic.split('/')
            machine_type = topic_parts[2]  # Extract "treadmill", "elliptical_trainer", etc.

            if machine_type in self.machines:
                self.update_availability(machine_type, availability)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Failed to decode machine availability data: {e}")

    def update_availability(self, machine_type, availability):
        machine_data = self.machines[machine_type]

        if availability == 1:  # Machine is occupied
            machine_data['occupied'] += 1
            machine_data['available'] -= 1
        elif availability == 0:  # Machine is available
            machine_data['occupied'] -= 1
            machine_data['available'] += 1

        # Publish the updated availability to MQTT topics
        self.publish_availability(machine_type)

    def publish_availability(self, machine_type):
        try:
            machine_data = self.machines[machine_type]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            topic = f"gym/group_availability/{machine_type}"
            message = {
                "topic": topic,
                "message": {
                    "device_id": "Machine availability block",
                    "timestamp": timestamp,
                    "data": {
                        "available": machine_data["available"],
                        "busy": machine_data["occupied"],
                        "total": machine_data["total"],
                        "unit": "count"
                    }
                }
            }

            self.client.publish(topic, json.dumps(message))
            print(f"Published availability data for {machine_type} to {topic}")
        except Exception as e:
            print(f"Failed to publish availability data: {e}")

    def stop(self):
        self.client.loop_stop()
        print("MQTT client stopped.")


def initialize_service(config_dict):
    # Register the service at startup
    register_service(config_dict,service.service_catalog_url)
    print("Machine Availability Service Initialized and Registered")

def stop_service(signum, frame):
    print("Stopping service...")
    delete_service("machine_availability",service.service_catalog_url)

    # Clean stop of the MQTT client
    service.stop()


if __name__ == "__main__":
    # Load configuration from config.json
    with open('config.json') as config_file:
        config = json.load(config_file)

    # Initialize the service with the loaded configuration
    service = MachineAvailabilityService(config)
    initialize_service(config)

    # Signal handler for clean stop
    signal.signal(signal.SIGINT, stop_service)

    # Start the MQTT client loop
    service.client.loop_start()
