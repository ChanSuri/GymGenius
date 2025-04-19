import time
import random
from datetime import datetime

class SimulatedDHT11Sensor:
    def __init__(self, room):
        """
        Initialize the sensor simulator for a specific room.
        
        :param room: Name of the room to simulate.
        """
        self.room = room
        self.rooms = {
            "entrance": {"type": "simulated", "temperature": 16.5, "humidity": 50.0},
            "cardio_room": {"type": "simulated", "temperature": 20.0, "humidity": 50.0},
            "lifting_room": {"type": "simulated", "temperature": 20.0, "humidity": 52.0},
            "changing_room": {"type": "simulated", "temperature": 29.0, "humidity": 55.0}
        }

        if room not in self.rooms:
            raise ValueError(f"Room '{room}' is not defined in the simulation.")

    def gradual_change(self, current_value, min_value, max_value, step=0.5):
        """Simulate gradual changes in temperature or humidity within a defined range."""
        change = random.uniform(-step, step)
        new_value = current_value + change
        return max(min(new_value, max_value), min_value)

    def generate_sensor_data(self, temperature, humidity):
        """Generate simulated data for the specified room in SenML format."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "device_id": f"DHT11_Sensor_{self.room}",
            "event_type": "environment",
            "type": "DHT11",
            "location": self.room,
            "status": "active",
            "endpoint": f"gym/environment/{self.room}",
            "time": current_time,
            "senml_record": {
                "bn": f"gym/environment/{self.room}",
                "e": [
                    {"n": "temperature", "u": "Cel", "t": current_time, "v": float("%.2f" % temperature)},
                    {"n": "humidity", "u": "%", "t": current_time, "v": float("%.2f" % humidity)}
                ]
            }
        }
        return data

    def simulate_dht11_sensor(self, seconds=0):
        """Simulate DHT11 sensor readings for a specified duration in seconds or a single event if seconds=0."""
        end_time = time.time() + seconds if seconds > 0 else time.time() + 1
        events = []

        sensor_info = self.rooms[self.room]

        while time.time() < end_time:
            # Gradually adjust temperature and humidity values
            temperature = self.gradual_change(sensor_info["temperature"], 13, 30)
            humidity = self.gradual_change(sensor_info["humidity"], 40, 70)

            # Update the simulated values
            sensor_info["temperature"] = temperature
            sensor_info["humidity"] = humidity

            # Generate SenML formatted data for the room
            event = self.generate_sensor_data(temperature, humidity)
            events.append(event)

            # If only one event is required, return immediately
            if seconds == 0:
                return events

            # Wait before generating the next reading
            time.sleep(20)

        return events

# Main section to demonstrate usage of SimulatedDHT11Sensor class
if __name__ == "__main__":
    try:
        # Ask user for the room and duration of the simulation
        room = input("Enter the room name to simulate: ").strip()
        simulation_time = int(input("Enter the duration in seconds for simulation (0 for a single event): "))

        # Initialize the sensor simulator for the specified room
        sensor = SimulatedDHT11Sensor(room=room)

        # Generate sensor data for the specified duration
        simulated_events = sensor.simulate_dht11_sensor(seconds=simulation_time)

        # Display each simulated event
        print("Simulated DHT11 Sensor Data:")
        for event in simulated_events:
            print(event)
    except ValueError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Simulation interrupted by user.")
