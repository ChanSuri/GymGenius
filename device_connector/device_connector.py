import cherrypy
import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from registration_functions import register_device

# URL of the Resource Catalog
RESOURCE_CATALOG_URL = 'http://localhost:8081/devices'

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_entry = "gym/occupancy/entry"
mqtt_topic_exit = "gym/occupancy/exit"
mqtt_topic_environment = "gym/environment"

class DeviceConnector:
    exposed = True

    def __init__(self):
        # Initialize the MQTT client
        self.client = mqtt.Client()
        self.client.connect(mqtt_broker, 1883, 60)
        self.client.loop_start()

        # Perform device checks at initialization
        self.check_and_delete_inactive_devices()

    def GET(self, *uri, **params):
        """Handles GET requests (not used in this case)"""
        return json.dumps({"message": "Welcome to the Gym Genius Device Connector"})

    def POST(self, *uri, **params):
        """Handles POST requests based on the type of request"""
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)

        # Check if the POST request is from the DHT11 sensor
        if "device_id" in input_data and "event_type" in input_data and input_data.get("event_type") == "environment":
            # Register the device if not already registered
            registration_response = self.register_device(input_data)
            registration_data = json.loads(registration_response)

            # If registration is successful, proceed with handling the MQTT event
            if registration_data["status"] == "success":
                return self.publish_environment_data(input_data)
            else:
                # Return the error response from the device registration
                return self.publish_environment_data(input_data) if registration_data["message"] == "Device already exists" else 500

        # Check if the POST request is from the entry/exit button
        if "device_id" in input_data and "event_type" in input_data and input_data["event_type"] in ["entry", "exit"]:
            # Call to register a new device
            registration_response = self.register_device(input_data)
            registration_data = json.loads(registration_response)

            # If registration is successful, proceed with handling the MQTT event
            if registration_data["status"] == "success":
                return self.publish_entry_exit_data(input_data)
            else:
                # Return the error response from the device registration
                return self.publish_entry_exit_data(input_data) if registration_data["message"] == "Device already exists" else 500

        else:
            raise cherrypy.HTTPError(400, "Invalid data format")

    def register_device(self, input_data):
        """Registers or updates a device in the Resource Catalog using the function from registration_functions.py"""
        device_id = input_data.get("device_id")
        device_type = input_data.get("type")
        location = input_data.get("location")
        status = input_data.get("status")
        endpoint = input_data.get("endpoint")
        time = input_data.get("time")

        if not device_id or not device_type or not location or not status or not endpoint:
            raise cherrypy.HTTPError(400, "All fields (device_id, type, location, status, endpoint) are required")

        # Use the register_device function from the registration_functions.py file
        try:
            register_device(device_id, device_type, location, status, endpoint, time)
            return json.dumps({"status": "success", "message": "Device registered/updated successfully"})
        except Exception as e:
            cherrypy.response.status = 500
            return json.dumps({"status": "error", "message": str(e)})
    
    def publish_environment_data(self, input_data):
        """Publish temperature and humidity data to MQTT"""
        try:
            senml_record = input_data.get("senml_record", {})
            
            # Convert the record to JSON and publish it to the MQTT topic
            self.client.publish(mqtt_topic_environment, json.dumps(senml_record))
            return json.dumps({"status": "success", "message": "Environment data published to MQTT"})
        
        except Exception as e:
            print(f"Error in publishing environment data: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def publish_entry_exit_data(self, input_data):
        """Handles entry/exit events by publishing them on MQTT"""
        event_type = input_data["event_type"]
        senml_record = input_data.get("senml_record", {})

        if event_type == "entry":
            self.client.publish(mqtt_topic_entry, json.dumps({"event": "entry", "senml_record": senml_record}))
            return json.dumps({"status": "success", "message": "Entry event published"})
        elif event_type == "exit":
            self.client.publish(mqtt_topic_exit, json.dumps({"event": "exit", "senml_record": senml_record}))
            return json.dumps({"status": "success", "message": "Exit event published"})
        else:
            raise cherrypy.HTTPError(400, "Invalid event type")

    def check_and_delete_inactive_devices(self):
        """Checks for inactive devices and deletes them if they haven't been updated in the last 3 days"""
        try:
            response = requests.get(RESOURCE_CATALOG_URL)
            if response.status_code == 200:
                device_registry = response.json().get("devices", [])
                current_time = datetime.now()

                for device in device_registry:
                    last_update_str = device.get("lastUpdate")
                    if last_update_str:
                        last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
                        if current_time - last_update > timedelta(days=3):
                            # Device inactive for more than 3 days, send DELETE request
                            self.delete_device(device.get("device_id"))

            else:
                print(f"Error retrieving the device registry: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"Connection error during GET request to the Resource Catalog: {e}")

    def delete_device(self, device_id):
        """Sends a DELETE request to remove an inactive device from the Resource Catalog"""
        if device_id:
            try:
                response = requests.delete(f"{RESOURCE_CATALOG_URL}/{device_id}")
                if response.status_code == 200:
                    print(f"Device {device_id} successfully deleted from the Resource Catalog.")
                else:
                    print(f"Error deleting device {device_id}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Connection error during DELETE request: {e}")
        else:
            print("Invalid device_id for deletion.")

if __name__ == '__main__':
    # CherryPy configuration with port and host settings
    cherrypy.config.update({'server.socket_port': 8082, 'server.socket_host': '0.0.0.0'})

    # Mount the DeviceConnector using MethodDispatcher
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }

    # Start the CherryPy server
    cherrypy.tree.mount(DeviceConnector(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
