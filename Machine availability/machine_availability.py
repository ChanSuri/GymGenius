import cherrypy
import paho.mqtt.client as mqtt
import json
import time
import requests
from datetime import datetime, timedelta
import signal
from registration_functions import register_service

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_availability = "gym/availability/#"  # Subscribe to all machine availability

class MachineAvailabilityService:
    exposed = True

    def __init__(self, machine_types):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.connect_mqtt()

        self.client.subscribe(mqtt_topic_availability)

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
        else:
            print(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with return code {rc}. Reconnecting...")
        self.connect_mqtt()

    def on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            availability = payload['e'][0]['v']  # Assuming the availability status is sent in the 'v' field
            
            # Extract machine type from topic, e.g. "gym/availability/treadmill/1"
            topic_parts = message.topic.split('/')
            machine_type = topic_parts[2]  # Extract "treadmill", "elliptical_trainer", etc.
            
            if machine_type in self.machines:
                self.update_availability(machine_type, availability)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Failed to decode machine availability data: {e}")

    def update_availability(self, machine_type, availability):
        machine_data = self.machines[machine_type]

        if availability == 1:  # Machine is occupied
            machine_data['occupied'] += 1
            machine_data['available'] -= 1
        elif availability == 0:  # Machine is available
            machine_data['occupied'] -= 1
            machine_data['available'] += 1

        # Save the aggregated data to a JSON file
        self.save_availability_to_file()

    def save_availability_to_file(self):
        try:
            with open('availability.json', 'w') as f:
                json.dump(self.machines, f, indent=4)
            print("Availability data saved to availability.json")
        except Exception as e:
            print(f"Failed to save availability data to file: {e}")

    # REST API to retrieve current machine availability status from the JSON file
    def GET(self, *uri, **params):
        try:
            with open('availability.json', 'r') as f:
                availability_data = json.load(f)
            return json.dumps({
                "status": "success",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "machines": availability_data
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": str(e)
            })

    def stop(self):
        self.client.loop_stop()
        print("MQTT client stopped.")


def initialize_service():
    # Register the service at startup
    service_id = "machine_availability"
    description = "Manages machine availability"
    status = "active"
    endpoint = "http://localhost:8085/machine_availability"
    register_service(service_id, description, status, endpoint)
    print("Machine Availability Service Initialized and Registered")

def stop_service(signum, frame):
    print("Stopping service...")
    cherrypy.engine.exit()

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
    
    # CherryPy configuration to expose the REST API
    cherrypy.config.update({'server.socket_port': 8085, 'server.socket_host': '0.0.0.0'})
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    }

    # Start the service
    cherrypy.tree.mount(service, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
