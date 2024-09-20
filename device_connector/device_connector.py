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
mqtt_topic_availability =  "gym/availability"
mqtt_topic_hvac_control = "gym/hvac/control"  # Topic for HVAC control commands
mqtt_topic_hvac_on_off = "gym/hvac/on_off"  # Topic for HVAC on/off commands

class DeviceConnector:
    exposed = True

    def __init__(self):
        # Initialize the MQTT client
        self.client = mqtt.Client()
        self.client.on_message = self.on_message  # Attach the on_message callback
        self.client.connect(mqtt_broker, 1883, 60)
        self.client.loop_start()

        # Subscribe to the HVAC control topics
        self.client.subscribe(mqtt_topic_hvac_control)
        self.client.subscribe(mqtt_topic_hvac_on_off)

        # Initialize HVAC status and temperature simulation
        self.hvac_state = 'off'  # HVAC is initially off
        self.hvac_mode = None    # No mode when HVAC is off
        self.hvac_last_turned_on = None  # Track when HVAC was last turned on

        self.real_temperature = None  # Actual temperature reported by the sensor
        self.simulated_temperature = None  # Simulated temperature (adjusted by HVAC)

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
                        "v": senml_record.get("e", {}).get("v")  # Preserve the availability value
                    }
                ]
            }

            # Convert the modified SenML record to JSON and publish it to MQTT
            self.client.publish(mqtt_topic_availability + "/" + machine_name, json.dumps(modified_senml_record))
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
                self.real_temperature = temperature  # Update the actual temperature from the sensor

                # Modify temperature based on HVAC status and residual effect
                modified_temperature = self.update_simulated_temperature()

                # Update the SenML record with the modified temperature
                for entry in senml_record["e"]:
                    if entry["n"] == "temperature":
                        entry["v"] = modified_temperature

            # Convert the record to JSON and publish it to the MQTT topic
            self.client.publish(mqtt_topic_environment + '/' + room, json.dumps(senml_record))
            return json.dumps({"status": "success", "message": "Environment data published to MQTT"})

        except Exception as e:
            print(f"Error in publishing environment data: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    def update_simulated_temperature(self):
        """Update the simulated temperature, considering HVAC state and residual effect."""
        if self.simulated_temperature is None:
            # Initialize the simulated temperature to the real temperature
            self.simulated_temperature = self.real_temperature

        # If HVAC is on, apply its effect on the temperature
        if self.hvac_state == 'on' and self.hvac_last_turned_on:
            elapsed_time = datetime.now() - self.hvac_last_turned_on
            minutes_running = elapsed_time.total_seconds() / 60

            # Apply the temperature change: 0.5 degrees per 15 minutes
            temp_change = (minutes_running // 15) * 0.5

            if self.hvac_mode == 'cool':
                # Decrease temperature for cooling
                self.simulated_temperature -= temp_change
            elif self.hvac_mode == 'heat':
                # Increase temperature for heating
                self.simulated_temperature += temp_change
        else:
            # HVAC is off: gradually bring the simulated temperature back to the real temperature
            if self.simulated_temperature < self.real_temperature:
                self.simulated_temperature += 0.1  # Gradually increase to real temp
            elif self.simulated_temperature > self.real_temperature:
                self.simulated_temperature -= 0.1  # Gradually decrease to real temp

        # Ensure the temperature stays within realistic bounds (e.g., 15°C to 35°C)
        self.simulated_temperature = max(min(self.simulated_temperature, 35), 15)
        return round(self.simulated_temperature, 2)

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

    def on_message(self, client, userdata, message):
        """Handles incoming MQTT messages, especially for HVAC control and on/off commands."""
        try:
            payload = json.loads(message.payload.decode())
            topic = message.topic

            if topic == mqtt_topic_hvac_control:
                control_command = payload['message']['data'].get('control_command')
                mode = payload['message']['data'].get('mode', self.hvac_mode)  # Use current mode if not specified

                if control_command == 'turn_on':
                    if self.hvac_state == 'off':
                        self.hvac_state = 'on'
                        self.hvac_last_turned_on = datetime.now()
                        self.hvac_mode = mode
                        print(f"HVAC is turning ON in {self.hvac_mode} mode.")
                    else:
                        print("HVAC is already ON.")
                elif control_command == 'turn_off':
                    if self.hvac_state == 'on':
                        self.hvac_state = 'off'
                        self.hvac_last_turned_on = None  # Reset the timer
                        self.hvac_mode = None  # No mode when HVAC is off
                        print("HVAC is turning OFF.")
                    else:
                        print("HVAC is already OFF.")
                else:
                    print(f"Unknown HVAC command: {control_command}")

            # Handle on/off command from the admin via the gym/hvac/on_off topic
            elif topic == mqtt_topic_hvac_on_off:
                state = payload['message']['data'].get('state', "").upper()

                if state == "OFF":
                    # Turn off HVAC if the state is OFF
                    if self.hvac_state == 'on':
                        self.hvac_state = 'off'
                        self.hvac_last_turned_on = None
                        self.hvac_mode = None
                        print("HVAC is turning OFF based on admin command.")
                    else:
                        print("HVAC is already OFF based on admin command.")
                elif state == "ON":
                    # Optionally, you can turn it on (if needed)
                    print("Admin command received: HVAC should be ON, but no action taken.")
                else:
                    print(f"Unknown state received: {state}")

        except Exception as e:
            print(f"Error in processing the message from topic {message.topic}: {e}")

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
