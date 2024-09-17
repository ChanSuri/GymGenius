
# NOW ALL BUILT INTO DEVICE_CONNECTOR.PY, TO BE REMOVED

# import json
# import time
# import random
# from dht11 import dhtDevice  # Import the DHT11 sensor object from the dht11.py file

# class Actuator:
#     """
#     Class used to control the HVAC actuator module.
#     Simulates an HVAC system with real temperature and humidity data from the DHT11 sensor.
#     """
#     def __init__(self, conf):
#         """
#         Parameters:
#         - conf: configuration file as a JSON dictionary.
#         """
#         self.config = conf
#         self.name = self.config["device_name"]
#         self.pin = int(self.config["pin"])  # Pin not used in the simulation
#         self.state = 'off'  # The HVAC starts off
#         self.mode = self.config.get("mode", "cool")  # Mode: cool or heat

#     def start_actuation(self):
#         """
#         Start the HVAC system, setting it to 'on' and controlling the mode (heat or cool).
#         """
#         if self.state == 'off':
#             self.state = 'on'
#             print(f"{self.name} is turning ON in {self.mode} mode.")
#             return 1
#         else:
#             return 0 
        
#     def stop_actuation(self):
#         """
#         Stop the HVAC system, setting it to 'off'.
#         """
#         if self.state == 'on':
#             self.state = 'off'
#             print(f"{self.name} is turning OFF.")
#             return 1
#         else:
#             return 0

#     def control_environment(self):
#         """
#         Simulate control of the environment based on the HVAC mode (cool/heat) 
#         and real sensor data from the DHT11 sensor.
#         """
#         try:
#             # Reading real data from the DHT11 sensor
#             temperature = dhtDevice.temperature
#             humidity = dhtDevice.humidity

#             # Check if sensor data is available
#             if temperature is None or humidity is None:
#                 print("Failed to retrieve data from DHT sensor")
#                 return None

#             print(f"Initial Temperature: {temperature}°C, Humidity: {humidity}%")

#             # If HVAC is on, adjust temperature and humidity based on the mode
#             if self.state == 'on':
#                 if self.mode == 'cool':
#                     # Cool the environment by reducing temperature
#                     temperature -= random.uniform(0.5, 1.5)
#                 elif self.mode == 'heat':
#                     # Heat the environment by increasing temperature
#                     temperature += random.uniform(0.5, 1.5)

#                 # Humidity always decreases when HVAC is on
#                 humidity -= random.uniform(0.5, 1.0)

#             # Apply realistic limits
#             temperature = max(min(temperature, 30), 15)  # Temperature between 15°C and 30°C
#             humidity = max(min(humidity, 60), 30)  # Humidity between 30% and 60%

#             return {
#                 "temperature": round(temperature, 2),
#                 "humidity": round(humidity, 2)
#             }

#         except Exception as e:
#             print(f"Error during sensor reading or control: {str(e)}")
#             return None
    
# # Program demo used for testing
# if __name__ == "__main__":
#     sample_conf = {
#         "device_name": "HVAC System",
#         "pin": 7,
#         "mode": "cool"  # You can change to 'heat' to simulate heating
#     }

#     hvac = Actuator(sample_conf)

#     while True:
#         env_data = hvac.control_environment()

#         if env_data:
#             temperature = env_data['temperature']
#             humidity = env_data['humidity']
#             print(f"Temperature: {temperature}, Humidity: {humidity}")

#             # Turn on HVAC if temperature is too high
#             if temperature > 28 and hvac.state == 'off':
#                 hvac.start_actuation()

#             # Turn off HVAC if temperature is below a certain value
#             if temperature < 24 and hvac.state == 'on':
#                 hvac.stop_actuation()

#         time.sleep(2)  # Interval between sensor readings
