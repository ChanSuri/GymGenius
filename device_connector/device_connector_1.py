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

class DeviceConnector:
    exposed = True

    def __init__(self, config):
        # Load configuration from config.json
        self.config = config
        self.service_catalog_url = self.config['service_catalog']  # Get service catalog URL from config.json
        self.resource_catalog_url = self.config['resource_catalog']  # Get resource catalog URL from config.json
        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()

        # Get rooms from service catalog
        self.rooms = self.get_rooms_from_service_catalog()

        # Initialize the MQTT client
        self.client = mqtt.Client()
        self.client.on_message = self.on_message  # Attach the on_message callback
        print(self.mqtt_broker, self.mqtt_port)
        try:
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
        except Exception as e:
            print(f"Failed to connect to MQTT Broker: {e}")
        self.client.loop_start()

        # Subscribe to the HVAC control topics for all rooms
        self.subscribe_to_topics()

        # Initialize HVAC status and mode for each room
        self.hvac_state = {room: 'off' for room in self.rooms}  # HVAC is initially off for all rooms
        self.hvac_mode = {room: None for room in self.rooms}  # No mode when HVAC is off
        self.hvac_last_turned_on = {room: None for room in self.rooms}  # Track when HVAC was last turned on per room

        self.real_temperature = {room: None for room in self.rooms}  # Actual temperature per room
        self.simulated_temperature = {room: None for room in self.rooms}  # Simulated temperature per room

        # Initialize sensors
        self.dht11_sensor = SimulatedDHT11Sensor()
        self.pir_sensor = SimulatedPIRSensor()
        self.button_sensor = SimulatedButtonSensor()

        # Perform device checks at initialization
        self.check_and_delete_inactive_devices()

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
        
    def get_rooms_from_service_catalog(self):
        """Retrieve rooms from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('roomsID')  # Return the list of room IDs
            else:
                raise Exception(f"Failed to get room information: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error getting room info from service catalog: {e}")
            return []    

    def subscribe_to_topics(self):
        """Subscribe to topics listed in the config file."""
        try:
            for topic_key, topic_value in self.config["subscribed_topics"].items():
                self.client.subscribe(topic_value)
                print(f"Subscribed to topic: {topic_value}")
        except KeyError as e:
            print(f"Error in subscribed_topics format: {e}")

    def simulate_and_publish_sensors(self):
        """Simulate sensor data and publish to MQTT."""
        while True:
            try:
                # Simulate DHT11 sensor readings
                dht11_events = self.dht11_sensor.simulate_dht11_sensors(seconds=0)
                for event in dht11_events:
                    self.register_and_publish(event, "environment")

                # Simulate PIR sensor readings
                pir_events = self.pir_sensor.simulate_usage(machine_type="cardio", machines_per_type=2, seconds=0)
                for event in pir_events:
                    self.register_and_publish(event, "availability")

                # Simulate Button sensor readings (entry/exit)
                button_events = self.button_sensor.simulate_events(seconds=0)
                for event in button_events:
                    self.register_and_publish(event, event["event_type"])

                # Wait for a while before next simulation
                time.sleep(5)
            except KeyboardInterrupt:
                print("Simulation interrupted by user.")
                break

    def register_and_publish(self, input_data, topic_type):
        """Register device and publish data to MQTT."""
        # Register the device if not already registered
        registration_response = self.register_device(input_data)
        registration_data = json.loads(registration_response)

        # If registration is successful, proceed with publishing the data
        if registration_data["status"] == "success" or registration_data["message"] == "Device registered/updated successfully":
            self.publish_data(input_data, topic_type)
        else:
            print(f"Device registration failed: {registration_data}")

    def register_device(self, input_data):
        """Registers or updates a device in the Resource Catalog using the function from registration_functions.py."""
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
            register_device(device_id, device_type, location, status, endpoint, time, self.resource_catalog_url)
            return json.dumps({"status": "success", "message": "Device registered/updated successfully"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def publish_data(self, input_data, topic_type):
        """Publish data to MQTT."""
        try:
            topic = self.config["published_topics"].get(topic_type, "").replace('<roomID>', input_data.get("location", ""))
            self.client.publish(topic, json.dumps(input_data["senml_record"]))
            print(f"Published data to topic: {topic}")
        except Exception as e:
            print(f"Error in publishing data: {e}")

    def on_message(self, client, userdata, message):
        """Handles incoming MQTT messages, especially for HVAC control and on/off commands."""
        try:
            payload = json.loads(message.payload.decode())
            print("Received payload:", payload)
            topic = message.topic
            room = topic.split('/')[-1]  # Extract the room name from the topic

            if f"gym/hvac/control/{room}" in topic:
                control_command = payload['message']['data'].get('control_command')
                mode = payload['message']['data'].get('mode', self.hvac_mode[room])  # Use current mode if not specified
            
                if control_command == 'turn_on':
                    if self.hvac_state[room] == 'off':
                        self.hvac_state[room] = 'on'
                        self.hvac_last_turned_on[room] = datetime.now()
                        self.hvac_mode[room] = mode
                        print(f"HVAC is turning ON in {self.hvac_mode[room]} mode for {room}.")
                    else:
                        print(f"HVAC is already ON for {room}.")
                elif control_command == 'turn_off':
                    if self.hvac_state[room] == 'on':
                        self.hvac_state[room] = 'off'
                        self.hvac_last_turned_on[room] = None  # Reset the timer
                        self.hvac_mode[room] = None  # No mode when HVAC is off
                        print(f"HVAC is turning OFF for {room}.")
                    else:
                        print(f"HVAC is already OFF for {room}.")
                else:
                    print(f"Unknown HVAC command: {control_command} for {room}")
        except Exception as e:
            print(f"Error in processing the message from topic {message.topic}: {e}")

if __name__ == '__main__':
    try:
        # Load configuration from config.json
        with open('config.json') as config_file:
            config = json.load(config_file)

        # Initialize the service
        service = DeviceConnector(config)
        initialize_service(config)

        # Start simulating and publishing sensor data
        service.simulate_and_publish_sensors()

    except Exception as e:
        print(f"Error in the main execution: {e}")
