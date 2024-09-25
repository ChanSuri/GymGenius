import paho.mqtt.client as mqtt
import time
import json
import datetime
import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LinearRegression
from registration_functions import register_service
import signal

# Global variable to track the current occupancy
current_occupancy = 0

# Matrices 9x7: 9 time slots (from 8:00 to 24:00 with 2-hour intervals), 7 days of the week
prediction_matrix = np.zeros((9, 7))

# List to store the training data for regression
X_train = []
Y_train = []

# Threshold to start training the model
min_training_samples = 2 * 9 * 7  # At least 2 data points for each slot-hour/day combination

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_entry = "gym/occupancy/entry"
mqtt_topic_exit = "gym/occupancy/exit"
mqtt_topic_current = "gym/occupancy/current"
mqtt_topic_prediction = "gym/occupancy/prediction"  # Topic for publishing predictions

# Model for regression
model = LinearRegression()

# URL di ThingSpeak per il file CSV
thingspeak_url = "https://localhost:8080/?channel=entrance"

class OccupancyService:

    def __init__(self):
        # MQTT client configuration
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(mqtt_broker, 1883, 60)
        self.client.loop_start()

    # Function triggered when MQTT client connects to the broker
    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result: " + str(rc))
        client.subscribe(mqtt_topic_entry)
        client.subscribe(mqtt_topic_exit)

    # Function triggered when a message is received
    def on_message(self, client, userdata, msg):
        global current_occupancy

        # Validate entry and exit messages
        if msg.topic == mqtt_topic_entry:
            self.increment_occupancy()
        elif msg.topic == mqtt_topic_exit:
            self.decrement_occupancy()

        # Fetch historical data from ThingSpeak
        self.fetch_historical_data()

        #Check if we can train the model (requires at least two data points per slot-hour/day)
        if len(X_train) >= min_training_samples:
            self.train_model()
            self.update_prediction()
        
        # Publish current occupancy to gym/occupancy/current
        self.publish_current_occupancy()

    # Function to increment occupancy with validation
    def increment_occupancy(self):
        global current_occupancy
        if current_occupancy < 1000:  # Arbitrary limit to prevent unrealistic occupancy
            current_occupancy += 1
            print(f"Increment: New occupancy = {current_occupancy}")
        else:
            print("Maximum occupancy reached, cannot increment.")

    # Function to decrement occupancy with validation
    def decrement_occupancy(self):
        global current_occupancy
        if current_occupancy > 0:
            current_occupancy -= 1
            print(f"Decrement: New occupancy = {current_occupancy}")
        else:
            print("Occupancy is already zero, cannot decrement.")

    # Function to fetch historical data from ThingSpeak
    def fetch_historical_data(self):
        response = requests.get(thingspeak_url)
        if response.status_code == 200:
            data = response.content.decode('utf-8')

            # Load CSV into pandas DataFrame
            df = pd.read_csv(pd.compat.StringIO(data))

            # Process the data
            for index, row in df.iterrows():
                timestamp = pd.to_datetime(row['created_at'])
                hour_slot = self.get_time_slot(timestamp.hour)
                day_of_week = timestamp.weekday()  # Monday = 0, Sunday = 6
                occupancy = row['current_occupancy']

                # Update training data
                X_train.append([hour_slot, day_of_week])
                Y_train.append(occupancy)
                print(f"Loaded data from ThingSpeak: Slot {hour_slot}, Day {day_of_week}, Occupancy: {occupancy}")
        else:
            print(f"Failed to fetch data from ThingSpeak, status code: {response.status_code}")

    # Function to determine the current time slot
    def get_time_slot(self, hour):
        if 8 <= hour < 10:
            return 0
        elif 10 <= hour < 12:
            return 1
        elif 12 <= hour < 14:
            return 2
        elif 14 <= hour < 16:
            return 3
        elif 16 <= hour < 18:
            return 4
        elif 18 <= hour < 20:
            return 5
        elif 20 <= hour < 22:
            return 6
        elif 22 <= hour < 24:
            return 7
        else:
            return 8  # Night slot for 24:00-8:00
        
    # Train the regression model with the historical data
    def train_model(self):
        global model
        X_train_np = np.array(X_train)
        Y_train_np = np.array(Y_train)

        # Fit the regression model
        model.fit(X_train_np, Y_train_np)
        print("Model trained with regression")

    # Function to update the prediction matrix using the trained regression model
    def update_prediction(self):
        global model
        for hour_slot in range(9):
            for day in range(7):
                # Predict occupancy for each slot-hour/day combination
                prediction_matrix[hour_slot, day] = model.predict([[hour_slot, day]])
        print(f"Prediction matrix updated: \n{prediction_matrix}")

        # Publish the updated prediction matrix to the corresponding MQTT topic
        self.publish_prediction()

    # Function to publish the current occupancy to the gym/occupancy/current topic
    def publish_current_occupancy(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = {
            "topic": mqtt_topic_current,
            "message": {
                "device_id": "DeviceConnector",
                "timestamp": now,
                "data": {
                    "current_occupancy": current_occupancy,
                    "unit": "count"
                }
            }
        }
        self.client.publish(mqtt_topic_current, json.dumps(message))
        print(f"Published current occupancy: {current_occupancy}")

    # Function to publish the prediction matrix to the gym/occupancy/prediction topic
    def publish_prediction(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = {
            "topic": mqtt_topic_prediction,
            "message": {
                "device_id": "Occupancy_block",
                "timestamp": now,
                "data": {
                    "prediction_matrix": prediction_matrix.tolist()
                }
            }
        }
        self.client.publish(mqtt_topic_prediction, json.dumps(message))
        print(f"Published prediction matrix to {mqtt_topic_prediction}")

    def stop(self):
        self.client.loop_stop()  # Stop MQTT loop
        self.client.disconnect()  # Disconnect from MQTT broker
        print("Service stopped")

def initialize_service():
    # Register the service at startup
    service_id = "occupancy_service"
    description = "Occupancy monitoring and prediction"
    status = "active"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    register_service(service_id, description, status, endpoint, timestamp)

def stop_service(signum, frame):
    print("Stopping service...")
    occupancy_service.stop()

# Main program to initialize the service
if __name__ == '__main__':
    initialize_service()

    # Configure the handler for graceful shutdown
    signal.signal(signal.SIGINT, stop_service)

    try:
        # Start MQTT loop (no REST server here)
        occupancy_service = OccupancyService()
        occupancy_service.client.loop_forever()
    finally:
        # Ensure that stop_service is called on exit
        occupancy_service.stop()
