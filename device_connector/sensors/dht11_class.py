import time
import random
from datetime import datetime, timezone

class SimulatedDHT11Sensor:
    def __init__(self):
        # Definition of rooms and their simulated temperature/humidity
        self.rooms = {
            "entrance": {"type": "simulated", "temperature": 16.5, "humidity": 50.0},
            "cardio_room": {"type": "simulated", "temperature": 20.0, "humidity": 50.0},
            "lifting_room": {"type": "simulated", "temperature": 20.0, "humidity": 52.0},
            "changing_room": {"type": "simulated", "temperature": 24.0, "humidity": 55.0}
        }

    def gradual_change(self, current_value, min_value, max_value, step=0.5):
        """Simulate gradual changes in temperature or humidity within a defined range."""
        change = random.uniform(-step, step)
        new_value = current_value + change
        return max(min(new_value, max_value), min_value)

    def generate_sensor_data(self, room, temperature, humidity):
        """Generate simulated data for a room in SenML format."""
        current_time = datetime.now(timezone.utc).isoformat()
        data = {
            "device_id": f"DHT11_Sensor_{room}",
            "event_type": "environment",
            "type": "DHT11",
            "location": room,
            "status": "active",
            "endpoint": f"gym/environment/{room}",
            "time": current_time,
            "senml_record": {
                "bn": f"gym/environment/{room}",
                "e": [
                    {"n": "temperature", "u": "Cel", "t": current_time, "v": temperature},
                    {"n": "humidity", "u": "%", "t": current_time, "v": humidity}
                ]
            }
        }
        return data

    def simulate_dht11_sensors(self, seconds=0):
        """Simulate DHT11 sensor readings for a specified duration in seconds or a single event if seconds=0."""
        end_time = time.time() + seconds if seconds > 0 else time.time() + 1
        events = []

        while time.time() < end_time:
            for room, sensor_info in self.rooms.items():
                # Gradually adjust temperature and humidity values
                temperature = self.gradual_change(sensor_info["temperature"], 13, 30)
                humidity = self.gradual_change(sensor_info["humidity"], 40, 70)

                # Update the simulated values
                sensor_info["temperature"] = temperature
                sensor_info["humidity"] = humidity

                # Generate SenML formatted data for each room
                event = self.generate_sensor_data(room, temperature, humidity)
                events.append(event)

                # If only one event is required, return immediately
                if seconds == 0:
                    return events

            # Wait before generating the next batch of readings
            time.sleep(5)

        return events

# Main section to demonstrate usage of SimulatedDHT11Sensor class
if __name__ == "__main__":
    sensor = SimulatedDHT11Sensor()

    try:
        # Ask user for the duration of the simulation in seconds
        simulation_time = int(input("Enter the duration in seconds for simulation (0 for a single event): "))
        
        # Generate sensor data for the specified duration
        simulated_events = sensor.simulate_dht11_sensors(seconds=simulation_time)
        
        # Display each simulated event
        print("Simulated DHT11 Sensor Data:")
        for event in simulated_events:
            print(event)
    except ValueError:
        print("Invalid input. Please enter a valid integer for the duration.")
    except KeyboardInterrupt:
        print("Simulation interrupted by user.")
