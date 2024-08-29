import cherrypy
import paho.mqtt.client as mqtt
import time
import json
import datetime
import numpy as np
import signal
from sklearn.linear_model import LinearRegression
from registration_functions import register_service

# Global variable to track the current occupancy
current_occupancy = 0

# Matrices 9x7: 9 time slots (from 8:00 to 24:00 with 2-hour intervals), 7 days of the week
prediction_matrix = np.zeros((9, 7))
historical_data = np.zeros((9, 7))  # Matrix to store historical data

# List to store the training data for regression
X_train = []
Y_train = []

# Threshold to start training the model
min_training_samples = 2 * 9 * 7  # At least 2 data points for each slot-hour/day combination

# MQTT Configuration
mqtt_broker = "test.mosquitto.org"
mqtt_topic_entry = "gym/occupancy/entry"
mqtt_topic_exit = "gym/occupancy/exit"

# Model for regression
model = LinearRegression()

class OccupancyService:
    exposed = True

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
        message = json.loads(msg.payload.decode())

        # Validate entry and exit messages
        if msg.topic == mqtt_topic_entry:
            self.increment_occupancy()
        elif msg.topic == mqtt_topic_exit:
            self.decrement_occupancy()

        # Record historical data and check for model training condition
        self.record_historical_data(current_occupancy)
        if self.can_train_model():
            self.train_model()
            self.update_prediction()

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

    # Function to record historical data associated with time slot and day
    def record_historical_data(self, occupancy):
        now = datetime.datetime.now()
        hour_slot = self.get_time_slot(now.hour)
        day_of_week = now.weekday()  # Monday = 0, Sunday = 6

        # Update historical data matrix with current occupancy
        historical_data[hour_slot, day_of_week] += occupancy
        print(f"Historical data updated: Slot {hour_slot}, Day {day_of_week}, Occupancy: {occupancy}")

        # Collect data for training: input (hour_slot, day_of_week), output (average occupancy)
        X_train.append([hour_slot, day_of_week])
        Y_train.append(historical_data[hour_slot, day_of_week] / max(1, historical_data[hour_slot, day_of_week]))

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

    # Check if we can train the model (requires at least two data points per slot-hour/day)
    def can_train_model(self):
        return len(X_train) >= min_training_samples

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
        self.save_prediction_to_file()

    # Function to save the prediction matrix to a file (prediction.json) at the end of the day
    def save_prediction_to_file(self):
        try:
            with open('prediction.json', 'w') as f:
                json.dump(prediction_matrix.tolist(), f)
            print("Prediction matrix saved to prediction.json")
        except Exception as e:
            print(f"Error saving prediction data to file: {e}")

    # REST API to retrieve the current occupancy and prediction matrix
    def GET(self, *uri, **params):
        try:
            with open('prediction.json', 'r') as f:
                prediction_data = json.load(f)
            response = {
                "status": "success",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "current_occupancy": current_occupancy,
                "prediction_matrix": prediction_data
            }
        except FileNotFoundError:
            response = {
                "status": "error",
                "message": "Prediction data not found."
            }
        return json.dumps(response)

def initialize_service():
    # Register the service at startup
    service_id = "occupancy_service"
    description = "Occupancy monitoring and prediction"
    status = "active"
    endpoint = "http://localhost:8083/occupancy"
    register_service(service_id, description, status, endpoint)

def stop_service(signum, frame):
    print("Stopping service...")
    cherrypy.engine.exit()

# CherryPy server configuration to expose the REST service
if __name__ == '__main__':
    initialize_service()

    # Configure the handler for graceful shutdown
    signal.signal(signal.SIGINT, stop_service)

    cherrypy.config.update({'server.socket_port': 8083, 'server.socket_host': '0.0.0.0'})

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        }
    }

    # Start the microservice
    cherrypy.tree.mount(OccupancyService(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()
