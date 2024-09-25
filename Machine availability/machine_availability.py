import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import signal
from registration_functions import *

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_availability = "gym/availability/#"  # Subscribe to all machine availability topics

class MachineAvailabilityService:
    def __init__(self, machine_types):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        # Initial machine status for all machine types
        self.machines = {
            machine_type: {"total": total, "available": total, "occupied": 0}
            for machine_type, total in machine_types.items()
        }

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
            self.client.subscribe(mqtt_topic_availability)  # Subscribe to all machine availability topics
        else:
            print(f"Failed to connect to MQTT broker. Return code: {rc}")
    
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


def initialize_service():
    # Register the service at startup
    service_id = "machine_availability"
    description = "Manages machine availability"
    status = "active"
    register_service(service_id, description, status, None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Machine Availability Service Initialized and Registered")

def stop_service(signum, frame):
    print("Stopping service...")
    delete_service("hvac_control")

    # Clean stop of the MQTT client
    service.stop()


if __name__ == "__main__":
    # Define the total number of machines for each type
    machine_types = {
        "treadmill": 5,
        "elliptical_trainer": 4,
        "stationary_bike": 6,
        "rowing_machine": 3,
        "cable_machine": 5,
        "leg_press_machine": 5,
        "smith_machine": 5,
        "lat_pulldown_machine": 5
    }

    # Initialize the service
    service = MachineAvailabilityService(machine_types)
    initialize_service()

    # Signal handler for clean stop
    signal.signal(signal.SIGINT, stop_service)
    
    # Start the MQTT client loop
    service.client.loop_start()
