import cherrypy
import json
import requests
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from registration_functions import *
import signal

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
        self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.client.loop_start()

        # Subscribe to the HVAC control topics for all rooms
        self.subscribe_to_topics()

       # Initialize HVAC status and mode for each room
        self.hvac_state = {room: 'off' for room in self.rooms}  # HVAC is initially off for all rooms
        self.hvac_mode = {room: None for room in self.rooms}  # No mode when HVAC is off
        self.hvac_last_turned_on = {room: None for room in self.rooms}  # Track when HVAC was last turned on per room

        self.real_temperature = {room: None for room in self.rooms}  # Actual temperature per room
        self.simulated_temperature = {room: None for room in self.rooms}  # Simulated temperature per room

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

    def GET(self, *uri, **params):
        """Handles GET requests (not used in this case)."""
        return json.dumps({"message": "Welcome to the Gym Genius Device Connector"})

    def POST(self, *uri, **params):
        """Handles POST requests based on the type of request."""
        body = cherrypy.request.body.read().decode('utf-8')
        input_data = json.loads(body)

        # Check if the POST request is from the DHT11 sensor
        if "device_id" in input_data and "event_type" in input_data and input_data.get("event_type") == "environment":
            # Register the device if not already registered
            registration_response = self.register_device(input_data)
            registration_data = json.loads(registration_response)

            # If registration is successful, modify and send temperature data
            if registration_data["status"] == "success" or registration_data["message"] == "Device registered/updated successfully":
                return self.publish_environment_data(input_data)
            else:
                # Return the error response from the device registration
                return json.dumps({"status": "error", "message": "Device registration failed"})

        # Check if the POST request is from the entry/exit button
        if "device_id" in input_data and "event_type" in input_data and input_data["event_type"] in ["entry", "exit"]:
            # Call to register a new device
            registration_response = self.register_device(input_data)
            registration_data = json.loads(registration_response)

            # If registration is successful, proceed with handling the MQTT event
            if registration_data["status"] == "success" or registration_data["message"] == "Device registered/updated successfully":
                return self.publish_entry_exit_data(input_data)
            else:
                # Return the error response from the device registration
                return json.dumps({"status": "error", "message": "Device registration failed"})
            
        # Check if the POST request is from the IR sensor
        if "device_id" in input_data and "event_type" in input_data and input_data["event_type"] == "availability":
            # Call to register a new device
            registration_response = self.register_device(input_data)
            registration_data = json.loads(registration_response)

            # If registration is successful, proceed with handling the MQTT event
            if registration_data["status"] == "success" or registration_data["message"] == "Device registered/updated successfully":
                return self.publish_availability_data(input_data)
            else:
                # Return the error response from the device registration
                return json.dumps({"status": "error", "message": "Device registration failed"})

        else:
            raise cherrypy.HTTPError(400, "Invalid data format")

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
            cherrypy.response.status = 500
            return json.dumps({"status": "error", "message": str(e)})
        
    def publish_availability_data(self, input_data):
        """Publish availability data to MQTT, modifying the SenML record with dynamic machine names."""
        try:
            # Extract SenML record and other necessary data from input_data
            senml_record = input_data.get("senml_record", {})
            current_time = input_data.get("time")

            # Dynamically determine the machine name from the 'bn' field or input_data
            base_name = senml_record.get("bn", "")  # e.g., "gym/availability/treadmill/1"
            # Extract machine name (e.g., "treadmill") from the basename
            machine_name = base_name.split('/')[-2] if base_name else "machine"

            # Create the modified SenML record with the dynamic machine name
            modified_senml_record = {
                "bn": base_name,
                "e": [
                    {
                        "n": f"{machine_name}_availability",  # Dynamically set machine availability name
                        "u": "binary",
                        "t": current_time,
                        "v": senml_record.get("v", None)
                    }
                ]
            }

            # Convert the modified SenML record to JSON and publish it to MQTT
            self.client.publish(self.config["published_topics"]["availability"].replace('<machineID>', machine_name), json.dumps(modified_senml_record))
            return json.dumps({"status": "success", "message": f"Availability data for {machine_name} published to MQTT"})

        except Exception as e:
            print(f"Error in publishing availability data: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def publish_environment_data(self, input_data):
        """Publish temperature and humidity data to MQTT, considering HVAC state and residual effects."""
        try:
            # Extract temperature and humidity from the sensor data
            senml_record = input_data.get("senml_record", {})
            temperature = next((e["v"] for e in senml_record["e"] if e["n"] == "temperature"), None)
            room = input_data.get("location")

            if temperature is not None:
                self.real_temperature[room] = temperature  # Update the actual temperature from the sensor

                # Modify temperature based on HVAC status and residual effect
                modified_temperature = self.update_simulated_temperature(room)

                # Update the SenML record with the modified temperature
                for entry in senml_record["e"]:
                    if entry["n"] == "temperature":
                        entry["v"] = modified_temperature

            # Convert the record to JSON and publish it to the MQTT topic
            self.client.publish(self.config["published_topics"]["environment"].replace('<roomID>', room), json.dumps(senml_record))
            return json.dumps({"status": "success", "message": "Environment data published to MQTT"})

        except Exception as e:
            print(f"Error in publishing environment data: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def update_simulated_temperature(self, room):
        """Update the simulated temperature, considering HVAC state and residual effect for a specific room."""
        if self.simulated_temperature[room] is None:
            # Initialize the simulated temperature to the real temperature
            self.simulated_temperature[room] = self.real_temperature[room]

        # If HVAC is on, apply its effect on the temperature
        if self.hvac_state[room] == 'on' and self.hvac_last_turned_on[room]:
            elapsed_time = datetime.now() - self.hvac_last_turned_on[room]
            minutes_running = elapsed_time.total_seconds() / 60

            # Apply the temperature change: 0.5 degrees per 15 minutes
            temp_change = (minutes_running // 15) * 0.5

            if self.hvac_mode[room] == 'cool':
                # Decrease temperature for cooling
                self.simulated_temperature[room] -= temp_change
            elif self.hvac_mode[room] == 'heat':
                # Increase temperature for heating
                self.simulated_temperature[room] += temp_change
        else:
            # HVAC is off: gradually bring the simulated temperature back to the real temperature
            if self.simulated_temperature[room] < self.real_temperature[room]:
                self.simulated_temperature[room] += 0.1  # Gradually increase to real temp
            elif self.simulated_temperature[room] > self.real_temperature[room]:
                self.simulated_temperature[room] -= 0.1  # Gradually decrease to real temp

        # Ensure the temperature stays within realistic bounds (e.g., 15°C to 35°C)
        self.simulated_temperature[room] = max(min(self.simulated_temperature[room], 35), 15)
        return round(self.simulated_temperature[room], 2)

    def publish_entry_exit_data(self, input_data):
        """Handles entry/exit events by publishing them on MQTT."""
        event_type = input_data["event_type"]
        senml_record = input_data.get("senml_record", {})

        if event_type == "entry":
            self.client.publish(self.config["published_topics"]["entries"], json.dumps({"event": "entry", "senml_record": senml_record}))
            return json.dumps({"status": "success", "message": "Entry event published"})
        elif event_type == "exit":
            self.client.publish(self.config["published_topics"]["exits"], json.dumps({"event": "exit", "senml_record": senml_record}))
            return json.dumps({"status": "success", "message": "Exit event published"})
        else:
            raise cherrypy.HTTPError(400, "Invalid event type")

    def on_message(self, client, userdata, message):
        """Handles incoming MQTT messages, especially for HVAC control and on/off commands."""
        try:
            payload = json.loads(message.payload.decode())
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

            # Handle on/off command from the admin via the gym/hvac/on_off/{room} topic
            elif f"gym/hvac/on_off/{room}" in topic:
                state = payload['message']['data'].get('state', "").upper()
                mode = payload['message']['data'].get('mode', None)

                if state == "OFF":
                    # Turn off HVAC if the state is OFF
                    if self.hvac_state[room] == 'on':
                        self.hvac_state[room] = 'off'
                        self.hvac_last_turned_on[room] = None
                        self.hvac_mode[room] = None
                        print(f"HVAC is turning OFF based on admin command for {room}.")
                    else:
                        print(f"HVAC is already OFF based on admin command for {room}.")
                elif state == "ON":
                    # Turn on HVAC and apply the mode if available
                    if self.hvac_state[room] == 'off':
                        self.hvac_state[room] = 'on'
                        self.hvac_last_turned_on[room] = datetime.now()
                        self.hvac_mode[room] = mode if mode else self.hvac_mode[room]
                        print(f"HVAC is turning ON in {self.hvac_mode[room]} mode based on admin command for {room}.")
                    else:
                        print(f"HVAC is already ON based on admin command for {room}.")
                else:
                    print(f"Unknown state received: {state} for {room}")

        except Exception as e:
            print(f"Error in processing the message from topic {message.topic}: {e}")

    def check_and_delete_inactive_devices(self):
        """Checks for inactive devices and deletes them if they haven't been updated in the last 3 days."""
        try:
            response = requests.get(self.resource_catalog_url)  # URL for resource catalog is loaded from config
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
        """Sends a DELETE request to remove an inactive device from the Resource Catalog."""
        if device_id:
            try:
                response = requests.delete(f"{self.resource_catalog_url}/{device_id}")
                if response.status_code == 200:
                    print(f"Device {device_id} successfully deleted from the Resource Catalog.")
                else:
                    print(f"Error deleting device {device_id}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Connection error during DELETE request: {e}")
        else:
            print("Invalid device_id for deletion.")

    def stop(self):
        self.client.loop_stop()
        print("MQTT client stopped.")        

def initialize_service(config_dict):
    """Initialize and register the service."""
    register_service(config_dict,config_dict["service_catalog_url"])
    print("Device Connector Service Initialized and Registered")

# def stop_service(signum, frame):
#     """Cleanly stop the service."""
#     with open('config.json') as config_file:
#         config = json.load(config_file)
#     print("Stopping service...")
#     delete_service("device_connector", config["service_catalog_url"])

if __name__ == '__main__':
    try:
        # Load configuration from config.json
        with open('config.json') as config_file:
            config = json.load(config_file)

        # Initialize the service
        service = DeviceConnector(config)
        initialize_service(config)

        # Signal handler for clean stop
        # signal.signal(signal.SIGINT, stop_service)
        # service.stop()

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
        cherrypy.tree.mount(service, '/', conf)
        cherrypy.engine.start()
        cherrypy.engine.block()

    except Exception as e:
        print(f"Error in the main execution: {e}")
    # finally:
    #     service.stop()
