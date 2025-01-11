import cherrypy
import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from sensors.dht11_class import SimulatedDHT11Sensor
from sensors.PIR_class import SimulatedPIRSensor
from sensors.button_class import SimulatedButtonSensor
from registration_functions import *
import time
import threading

class DeviceConnector:
    exposed = True

    def __init__(self, config):
        # Load configuration
        self.config = config
        self.service_catalog_url = self.config['service_catalog']
        self.resource_catalog_url = self.config['resource_catalog']
        self.simulation_params = self.config.get("simulation_parameters", {})
        self.location = self.config.get("location", "unknown")

        # HVAC states and sensors
        self.hvac_state = 'off'  # HVAC is initially off
        self.hvac_mode = None  # No mode when HVAC is off
        self.hvac_last_turned_on = None

        self.real_temperature = {}  # Actual temperature from sensors
        self.simulated_temperature = {}  # Adjusted temperature

        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()
        self.client = mqtt.Client()
        self.client.on_message = self.on_message

        try:
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
        except Exception as e:
            print(f"MQTT connection error: {e}")
        self.client.loop_start()

        self.subscribe_to_topics()

        # Enable required sensors
        self.enable_sensors()

        # Perform device checks at initialization
        self.check_and_delete_inactive_devices()

    def get_mqtt_info_from_service_catalog(self):
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('brokerIP'), catalog.get('brokerPort')
            else:
                raise Exception(f"Error retrieving MQTT info: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Connection error to Service Catalog: {e}")
            return None, None

    def subscribe_to_topics(self):
        try:
            for topic_key, topic_value in self.config["subscribed_topics"].items():
                self.client.subscribe(topic_value)
                print(f"Subscribed to topic: {topic_value}")
        except KeyError as e:
            print(f"Error in topics: {e}")

    def enable_sensors(self):
        self.sensors = {}
        if self.config.get("enable_dht11", False):
            self.sensors["dht11"] = SimulatedDHT11Sensor(self.location)
        if self.config.get("enable_pir", False):
            self.sensors["pir"] = SimulatedPIRSensor(self.location)
        if self.config.get("enable_button", False):
            self.sensors["button"] = SimulatedButtonSensor()

    def simulate_and_publish_sensors(self):
        while True:
            try:
                if "dht11" in self.sensors:
                    events = self.sensors["dht11"].simulate_dht11_sensor(seconds=self.simulation_params.get("dht11_seconds", 5))
                    for event in events:
                        self.register_and_publish(event, "environment")

                if "pir" in self.sensors:
                    events = self.sensors["pir"].simulate_usage(
                        machine_type=self.simulation_params.get("pir_machine_type", "unknown"),
                        machines_per_type=self.simulation_params.get("pir_machines_per_type", 1),
                        seconds=self.simulation_params.get("pir_seconds", 5))
                    for event in events:
                        self.register_and_publish(event, "availability")

                if "button" in self.sensors:
                    events = self.sensors["button"].simulate_events(seconds=self.simulation_params.get("button_seconds", 5))
                    for event in events:
                        self.register_and_publish(event, event["event_type"])

                time.sleep(5)
            except KeyboardInterrupt:
                print("Simulation interrupted")
                break

    def register_and_publish(self, input_data, topic_type):
        """Register device and publish data to MQTT."""
        registration_response = self.register_device(input_data)
        registration_data = json.loads(registration_response)

        if registration_data["status"] == "success" or registration_data["message"] == "Device registered/updated successfully":
            if topic_type == "environment":
                self.publish_environment_data(input_data)
            elif topic_type == "availability":
                self.publish_data(input_data, topic_type)
            else:
                self.publish_data_occupancy(input_data, topic_type)
        else:
            print(f"Device registration failed: {registration_data}")

    def register_device(self, input_data):
        """Register or update device in the Resource Catalog."""
        device_id = input_data.get("device_id")
        device_type = input_data.get("type")
        status = input_data.get("status")
        endpoint = input_data.get("endpoint")
        time = input_data.get("time")

        if not device_id or not device_type or not status or not endpoint:
            raise ValueError("Missing required fields for device registration")

        try:
            register_device(device_id, device_type, self.location, status, endpoint, time, self.resource_catalog_url)
            return json.dumps({"status": "success", "message": "Device registered/updated successfully"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def publish_data(self, input_data, topic_type):
        try:
            topic = self.config["published_topics"].get(topic_type, "")
            topic = topic.replace('<machineID>', input_data.get("device_id", "unknown"))
            topic = topic.replace('<roomID>', input_data.get("location", "unknown"))
            
            senml_record = input_data.get("senml_record")
            if senml_record is None:
                print("Error: Missing 'senml_record' in input_data.")
                return

            self.client.publish(topic, json.dumps(senml_record))
            print(f"Published data to topic: {topic}")
        except Exception as e:
            print(f"Error in publishing data to topic '{topic_type}': {e}")

    def publish_data_occupancy(self, input_data, topic_type):
        """Publish data to MQTT."""
        try:
            if topic_type == "entry":
                topic = self.config["published_topics"]["entries"]
            elif topic_type == "exit":
                topic = self.config["published_topics"]["exits"]
            else:
                topic = self.config["published_topics"].get(topic_type, "")
                topic = topic.replace('<roomID>', input_data.get("location", ""))

            print(f"Publishing to topic: {topic}")
            self.client.publish(topic, json.dumps(input_data["senml_record"]))
            print(f"Published data to topic: {topic}")
        except Exception as e:
            print(f"Error in publishing data: {e}")  

    def publish_environment_data(self, input_data):
        """Publish temperature and humidity data to MQTT, considering HVAC state and residual effects."""
        try:
            # Extract temperature and humidity from the sensor data
            senml_record = input_data.get("senml_record", {})
            temperature = next((e["v"] for e in senml_record["e"] if e["n"] == "temperature"), None)
            room = input_data.get("location")

            if room and temperature is not None:
                self.real_temperature[room] = temperature  # Update the actual temperature from the sensor

                # Modify temperature based on HVAC status and residual effect
                modified_temperature = self.update_simulated_temperature(room)

                # Update the SenML record with the modified temperature
                for entry in senml_record["e"]:
                    if entry["n"] == "temperature":
                        entry["v"] = modified_temperature

                # Convert the record to JSON and publish it to the MQTT topic
                topic = self.config["published_topics"]["environment"].replace('<roomID>', room)
                print(f"Publishing to topic: {topic}")
                self.client.publish(topic, json.dumps(senml_record))
                return json.dumps({"status": "success", "message": "Environment data published to MQTT"})

            else:
                raise ValueError("Missing room or temperature data.")

        except Exception as e:
            print(f"Error in publishing environment data: {e}")
            return json.dumps({"status": "error", "message": str(e)})
              

    def update_simulated_temperature(self, room):
        """Update the simulated temperature for a specific room based on HVAC state and residual effects."""
        if room not in self.simulated_temperature:
            # Initialize simulated temperature for the room
            self.simulated_temperature[room] = self.real_temperature.get(room, 20.0)

        if self.hvac_state == 'on' and self.hvac_last_turned_on:
            elapsed_time = datetime.now() - self.hvac_last_turned_on
            minutes_running = elapsed_time.total_seconds() / 60

            # Apply HVAC effects: e.g., 0.5 degrees per 15 minutes
            temp_change = (minutes_running // 15) * 0.5

            if self.hvac_mode == 'cool':
                self.simulated_temperature[room] -= temp_change
            elif self.hvac_mode == 'heat':
                self.simulated_temperature[room] += temp_change
        else:
            # Gradual return to real temperature
            if self.simulated_temperature[room] < self.real_temperature.get(room, 20.0):
                self.simulated_temperature[room] += 0.1
            elif self.simulated_temperature[room] > self.real_temperature.get(room, 20.0):
                self.simulated_temperature[room] -= 0.1

        # Clamp temperature to realistic bounds
        self.simulated_temperature[room] = max(min(self.simulated_temperature[room], 35), 15)
        return round(self.simulated_temperature[room], 2)


    def check_and_delete_inactive_devices(self):
        """Checks for inactive devices and deletes them if they haven't been updated in the last 3 days."""
        try:
            response = requests.get(self.resource_catalog_url)  # URL for resource catalog is loaded from config 
            if response.status_code == 200:
                device_registry = response.json().get("devices", [])
                response = requests.get(self.resource_catalog_url)
                current_time = datetime.now()

                for device in device_registry["devices"]:
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
        """Deletes an inactive device from the Resource Catalog."""
        if device_id:
            try:
                response = requests.delete(f"{self.resource_catalog_url}/{device_id}")
                if response.status_code == 200:
                    print(f"Device {device_id} successfully deleted.")
                else:
                    print(f"Error deleting device {device_id}: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Error during DELETE request: {e}")
        else:
            print("Invalid device_id for deletion.")

    def on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            print(f"Received payload: {payload}")
            topic = message.topic

            if f"gym/hvac/control/{self.location}" in topic:
                control_command = payload.get('control_command')
                mode = payload.get('mode', self.hvac_mode)

                if control_command == 'turn_on':
                    if self.hvac_state == 'off':
                        self.hvac_state = 'on'
                        self.hvac_last_turned_on = datetime.now()
                        self.hvac_mode = mode
                        print(f"HVAC turned ON in {self.hvac_mode} mode.")
                elif control_command == 'turn_off':
                    if self.hvac_state == 'on':
                        self.hvac_state = 'off'
                        self.hvac_last_turned_on = None
                        self.hvac_mode = None
                        print("HVAC turned OFF.")
                else:
                    print(f"Unknown HVAC command: {control_command}")
        except Exception as e:
            print(f"Error processing message: {e}")

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) == 0:
            return {"status": "error", "message": "No endpoint specified."}

        if uri[0] == "environment":
            temperature = self.simulated_temperature
            humidity = self.real_temperature

            if temperature is None or humidity is None:
                return {"status": "error", "message": "No data available."}

            return {
                "status": "success",
                "senml_record": {
                    "e": [
                        {"n": "temperature", "u": "Cel", "v": temperature},
                        {"n": "humidity", "u": "%", "v": humidity}
                    ]
                },
                "location": self.location
            }

        if uri[0] == "hvac_status":
            return {
                "status": "success",
                "hvac_state": self.hvac_state,
                "hvac_mode": self.hvac_mode,
                "location": self.location
            }

        return {"status": "error", "message": f"Unknown endpoint: {uri[0]}"}

    def start_simulation_thread(self):
        """Start the thread for sensors' simulation"""
        self.simulation_thread = threading.Thread(target=self.simulate_and_publish_sensors)
        self.simulation_thread.daemon = True  # Thread closes when the main program ends.
        self.simulation_thread.start()

    def stop(self):
        self.client.loop_stop()
        print("MQTT client stopped")

def initialize_service(config_dict):
    """Initialize and register the service."""
    register_service(config_dict, config_dict["service_catalog"])
    print("Device Connector Service Initialized and Registered")        

if __name__ == '__main__':
    try:
        # with open('C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\device_connector_lifting_room\\config_device_connector_lifting_room.json') as config_file:
        with open('device_connector_lifting_room/config_device_connector_lifting_room.json') as config_file:
            config = json.load(config_file)

        service = DeviceConnector(config)
        initialize_service(config)

        service.start_simulation_thread()

        # CherryPy configuration with port and host settings
        cherrypy.config.update({'server.socket_port': 8095, 'server.socket_host': '0.0.0.0'})

        # Mount the DeviceConnector using MethodDispatcher
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True
            }
        }

        # Start the CherryPy server
        cherrypy.tree.mount(service, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()

    except Exception as e:
        print(f"Error in the main execution: {e}")
    # finally:
    #     service.stop()