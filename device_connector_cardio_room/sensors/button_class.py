import time
import datetime
import random

class SimulatedButtonSensor:
    def __init__(self):
        # Unique IDs for simulated devices
        self.entrance_device_id = "EntranceSensor001"
        self.exit_device_id = "ExitSensor001"

        # Entrance and exit counters
        self.entrance_count = 0
        self.exit_count = 0

        # Base SenML records for entrance and exit buttons
        self.entrance_base_record = {
            "bn": "gym/occupancy/entrance",
            "bt": 0,
            "n": "push-button-enter",
            "u": "count",
            "v": 0
        }
        
        self.exit_base_record = {
            "bn": "gym/occupancy/exit",
            "bt": 0,
            "n": "push-button-exit",
            "u": "count",
            "v": 0
        }

    # Method to simulate an entry event and return the SenML record
    def simulate_entry_event(self):
        self.entrance_count += 1
        record = self.entrance_base_record.copy()
        record["bt"] = time.time()
        record["v"] = self.entrance_count
        data = {
            "device_id": self.entrance_device_id,
            "event_type": "entry",
            "type": record["n"],
            "location": "entrance",
            "status": "active",
            "endpoint": record["bn"],
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "senml_record": record
        }
        return data

    # Method to simulate an exit event and return the SenML record
    def simulate_exit_event(self):
        if self.exit_count < self.entrance_count:  # Ensures exits do not exceed entries
            self.exit_count += 1
            record = self.exit_base_record.copy()
            record["bt"] = time.time()
            record["v"] = self.exit_count
            data = {
                "device_id": self.exit_device_id,
                "event_type": "exit",
                "type": record["n"],
                "location": "entrance",
                "status": "active",
                "endpoint": record["bn"],
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "senml_record": record
            }
            return data
        return None  # No exit event if exit_count exceeds entrance_count

    # Method to simulate events for a given number of seconds or a single event if x == 0
    def simulate_events(self, seconds=0):
        end_time = time.time() + seconds if seconds > 0 else time.time() + 1
        events = []

        while time.time() < end_time:
            if self.entrance_count > self.exit_count:
                action = random.choice(["entry", "exit"])
            else:
                action = "entry"  # Force entry if exits have matched or exceeded entries

            consecutive_events = random.randint(1, 5)

            if action == "entry":
                for _ in range(consecutive_events):
                    event = self.simulate_entry_event()
                    events.append(event)
                    time.sleep(random.uniform(1, 3))
                    if seconds == 0:
                        return events
            else:
                for _ in range(consecutive_events):
                    event = self.simulate_exit_event()
                    if event:
                        events.append(event)
                        time.sleep(random.uniform(1, 3))
                    else:
                        break  # Stop exits if they exceed entries
                    if seconds == 0:
                        return events

            time.sleep(random.uniform(5, 10))

        return events

# Main section to demonstrate usage of SimulatedButtonSensor class
if __name__ == "__main__":
    sensor = SimulatedButtonSensor()
    
    # Simulate events based on user input
    try:
        # Request user input to specify simulation duration in seconds
        simulation_time = int(input("Enter the duration in seconds for simulation (0 for a single event): "))
        
        # Generate events for the specified duration
        simulated_events = sensor.simulate_events(seconds=simulation_time)
        
        # Display each simulated event
        print("Simulated Events:")
        for event in simulated_events:
            print(event)
    except ValueError:
        print("Invalid input. Please enter a valid integer for the duration.")
    except KeyboardInterrupt:
        print("Simulation interrupted by user.")
