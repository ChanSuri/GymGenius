import paho.mqtt.client as mqtt
import time
import json
import datetime
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LinearRegression
from registration_functions import *
import signal
import pandas as pd
import io

# Global variables
current_occupancy = 0
X_train = []
Y_train = []
min_training_samples = None  # Will be calculated based on the number of time slots

# Model for regression
model = LinearRegression()

# Class to manage occupancy
class OccupancyService:

    def __init__(self, config):
        self.config = config
        self.service_catalog_url = config['service_catalog']  # Retrieve the service catalog URL from config.json
        self.mqtt_broker, self.mqtt_port = self.get_mqtt_info_from_service_catalog()  # Retrieve broker and port
        self.time_slots = self.get_time_slots_from_service_catalog()
        self.thing_speak_url = self.get_thingspeak_url_from_service_catalog()

        # Calculate min_training_samples based on the number of time slots and days in a week
        global min_training_samples
        #min_training_samples = 2 * len(self.time_slots) * 7  # 2 data points per slot-hour/day combination
        min_training_samples = 2

        # Initialize the prediction matrix (dynamic based on time slots)
        self.prediction_matrix = np.zeros((len(self.time_slots), 7))

        # MQTT client configuration
        self.client = mqtt.Client()
        self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        # self.client.loop_start()

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

    def get_time_slots_from_service_catalog(self):
        """Retrieve time slots configuration from the service catalog."""
        try:
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                return catalog.get('time_slots')
            else:
                raise Exception(f"Failed to get time slots: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving time slots from service catalog: {e}")
            return {}

    def get_thingspeak_url_from_service_catalog(self):
        """Retrieve ThingSpeak URL by looking for the service with serviceid 'thingspeak_adaptor'."""
        try:
            # Get the full catalog from the service catalog URL
            response = requests.get(self.service_catalog_url)
            if response.status_code == 200:
                service_catalog = response.json()
                catalog = service_catalog.get('catalog', {})
                services = catalog.get('services', [])
                
                # Find the service with serviceid = "thingspeak_reader"
                for service in services:
                    if service.get("service_id") == "thingspeak_reader": #before was thingspeak_adaptor
                        print(service.get("endpoint", None))
                        return service.get("endpoint", None)  # Return the endpoint if found

                # If the service is not found, return None or raise an exception
                raise Exception(f"Service 'thingspeak_reader' not found in the service catalog.")
            else:
                raise Exception(f"Failed to fetch services from catalog: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving ThingSpeak URL: {e}")
            return None

    def on_connect(self, client, userdata, flags, rc):
        print(rc)
        print(self.mqtt_broker, self.mqtt_port)
        if rc == 0: #rc = 5 perchè?
            for topic_key, topic_value in self.config["subscribed_topics"].items():
                client.subscribe(topic_value)
                print(f"Subscribed to topic: {topic_value}")
        else:
            (f"failed to connect to MQTT broker. Return code: {rc}")

    def on_message(self, client, userdata, msg):
        global current_occupancy

        # Validate entry and exit messages
        if msg.topic == self.config["subscribed_topics"]["entries"]:
            self.increment_occupancy()
        elif msg.topic == self.config["subscribed_topics"]["exits"]:
            self.decrement_occupancy()

        # Fetch historical data from ThingSpeak
        self.fetch_historical_data()

        # Check if we can train the model
        if len(X_train) >= min_training_samples: #non entra nell'if
            self.train_model()
            self.update_prediction()

        # Publish current occupancy
        self.publish_current_occupancy()

    def increment_occupancy(self):
        global current_occupancy
        if current_occupancy < 1000:
            current_occupancy += 1
            print(f"Increment: New occupancy = {current_occupancy}")
        else:
            print("Maximum occupancy reached, cannot increment.")

    def decrement_occupancy(self):
        global current_occupancy
        if current_occupancy > 0:
            current_occupancy -= 1
            print(f"Decrement: New occupancy = {current_occupancy}")
        else:
            print("Occupancy is already zero, cannot decrement.")

    def fetch_historical_data(self):
        """Fetch historical data from ThingSpeak."""
        print(self.thing_speak_url)
        if not self.thing_speak_url:
            print("ThingSpeak URL not available.")
            return

        response = requests.get(self.thing_speak_url)
        if response.status_code == 200:
            data = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(data)) #errore 

            for index, row in df.iterrows():
                timestamp = pd.to_datetime(row['created_at'])
                hour_slot = self.get_time_slot(timestamp.hour)
                day_of_week = timestamp.weekday()
                occupancy = row['current_occupancy']

                # Update training data
                X_train.append([hour_slot, day_of_week])
                Y_train.append(occupancy)
                print(f"Loaded data from ThingSpeak: Slot {hour_slot}, Day {day_of_week}, Occupancy: {occupancy}")
        else:
            print(f"Failed to fetch data from ThingSpeak, status code: {response.status_code}")

    def get_time_slot(self, hour):
        """Determine the time slot based on the hour using the time slots from the service catalog."""
        for slot, time_range in self.time_slots.items():
            start_hour = int(time_range["start"].split(":")[0])
            end_hour = int(time_range["end"].split(":")[0])
            if start_hour <= hour < end_hour:
                return int(slot)
        return len(self.time_slots) - 1  # Default to last slot if no match

    def train_model(self):
        global model
        X_train_np = np.array(X_train)
        Y_train_np = np.array(Y_train)

        model.fit(X_train_np, Y_train_np)
        print("Model trained with regression")

    def update_prediction(self):
        global model
        for hour_slot in range(len(self.time_slots)):
            for day in range(7):
                self.prediction_matrix[hour_slot, day] = model.predict([[hour_slot, day]])
        print(f"Prediction matrix updated: \n{self.prediction_matrix}")
        self.publish_prediction()

    def publish_current_occupancy(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #datetime.now errore
        message = {
            "topic": self.config["published_topics"]["current_occupancy"],
            "message": {
                "device_id": "DeviceConnector",
                "timestamp": now,
                "data": {
                    "current_occupancy": current_occupancy,
                    "unit": "count"
                }
            }
        }
        self.client.publish(self.config["published_topics"]["current_occupancy"], json.dumps(message))
        print(f"Published current occupancy: {current_occupancy}")

    def publish_prediction(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = {
            "topic": self.config["published_topics"]["prediction"],
            "message": {
                "device_id": "Occupancy_block",
                "timestamp": now,
                "data": {
                    "prediction_matrix": self.prediction_matrix.tolist()
                }
            }
        }
        self.client.publish(self.config["published_topics"]["prediction"], json.dumps(message))
        print(f"Published prediction matrix to {self.config['published_topics']['prediction']}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("Service stopped")

def initialize_service(config_dict):
    """Initialize and register the service."""
    register_service(config_dict, config_dict["service_catalog"])
    print("Occupancy Service Initialized and Registered")

def stop_service(signum, frame):
    with open('config.json') as f:
        config_dict = json.load(f)
    print("Stopping service...")
    delete_service("occupancy", config_dict["service_catalog"])

if __name__ == '__main__':
    # Open config.json once and pass it to both functions
    # with open('C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\Occupancy_monitoring_and_access_control\\config.json') as f:
    with open('config.json') as f:
        config_dict = json.load(f)

    # Initialize the service with the loaded configuration
    initialize_service(config_dict)

    # Graceful shutdown handler
    signal.signal(signal.SIGINT, stop_service)

    occupancy_service = OccupancyService(config=config_dict)
    occupancy_service.client.loop_forever()
