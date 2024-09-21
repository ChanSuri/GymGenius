# import RPi.GPIO as GPIO
# import time
# import json
# import requests

# # GPIO setup for the button
# button_pin = 23
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# # URL of the device connector
# device_connector_url = "http://localhost:8082"

# # Button press counter and previous state
# button_press_count = 0
# last_button_state = False

# # Unique identifier of the device
# device_id = "ExitSensor001"  # Replace with your device ID

# # SenML record template for the button
# base_record = {
#     "bn": "GymGenius/Occupancy/Exit",  # Unique identifier for the button
#     "bt": 0,  # Base time
#     "n": "push-button-exit",  # Sensor name
#     "u": "count",  # Unit of measure
#     "v": 0  # Value
# }

# # Function to write the SenML record to a file
# def write_senml_record(count):
#     record = base_record.copy()
#     record["bt"] = time.time()
#     record["v"] = count
#     with open('exit_count.senml', 'w') as file:
#         json.dump([record], file, indent=4)

# # Function to send an exit event to the device connector
# def send_exit_event():
#     try:
#         # Create the SenML record
#         record = base_record.copy()
#         record["bt"] = time.time()
#         record["v"] = button_press_count

#         # Send the record to the device connector as part of the POST request
#         data = {
#             "device_id": device_id,  # Also send the device ID
#             "event_type": "exit",
#             "type": record["n"],
#             "location": "entrance",
#             "status": "active",
#             "endpoint": record["bn"],
#             "senml_record": record
#         }
#         response = requests.post(f"{device_connector_url}/", json=data)
#         if response.status_code == 200:
#             print("Exit event sent successfully")
#         else:
#             print(f"Error sending exit event: {response.status_code}")
#     except Exception as e:
#         print(f"Error: {e}")

# # Main program
# try:
#     while True:
#         button_state = GPIO.input(button_pin)
#         if button_state != last_button_state:
#             if button_state == False:  # Button pressed (assuming active low)
#                 button_press_count += 1
#                 print(f"Button pressed {button_press_count} times")

#                 # Write the event in SenML format to the local file
#                 write_senml_record(button_press_count)

#                 # Send the event to the device connector
#                 send_exit_event()

#             last_button_state = button_state
#         time.sleep(0.05)
# except KeyboardInterrupt:
#     GPIO.cleanup()
