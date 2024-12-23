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
                        self.publish_data(event, "environment")

                if "pir" in self.sensors:
                    events = self.sensors["pir"].simulate_usage(
                        machine_type=self.simulation_params.get("pir_machine_type", "unkown"),
                        machines_per_type=self.simulation_params.get("pir_machines_per_type", 1),
                        seconds=self.simulation_params.get("pir_seconds", 5))
                    for event in events:
                        self.publish_data(event, "availability")

                if "button" in self.sensors:
                    events = self.sensors["button"].simulate_events(seconds=self.simulation_params.get("button_seconds", 5))
                    for event in events:
                        self.publish_data(event, event["event_type"])

                time.sleep(5)
            except KeyboardInterrupt:
                print("Simulation interrupted")
                break

    def publish_data(self, data, topic_type):
        try:
            topic = self.config["published_topics"].get(topic_type, "").replace("<roomID>", self.location)
            self.client.publish(topic, json.dumps(data))
            print(f"Published to {topic}: {data}")
        except Exception as e:
            print(f"Error in publishing: {e}")

    def on_message(self, client, userdata, message):
        print(f"Received message: {message.payload.decode()}")

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        return {"status": "success", "location": self.location}

    def stop(self):
        self.client.loop_stop()
        print("MQTT client stopped")

if __name__ == '__main__':
    with open('config_device_connector_entrance.json') as config_file:
        config = json.load(config_file)
    service = DeviceConnector(config)
    threading.Thread(target=service.simulate_and_publish_sensors, daemon=True).start()
    cherrypy.config.update({'server.socket_port': 8083})
    cherrypy.tree.mount(service, '/', {'/': {'tools.sessions.on': True}})
    cherrypy.engine.start()
    cherrypy.engine.block()
