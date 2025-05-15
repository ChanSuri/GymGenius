import time
import random
from datetime import datetime

class SimulatedPIRSensor:
    def __init__(self, location):
        # Definition of simulated machines
        self.cardio_machines = ["treadmill", "elliptical_trainer", "stationary_bike", "rowing_machine"]
        self.lifting_machines = ["cable_machine", "leg_press_machine", "smith_machine", "lat_pulldown_machine"]
        self.location = location

    def generate_sensor_data(self, value, machine, machine_number):
        """Generate simulated availability data in SenML format for a machine."""
        record = {
            "bn": f"gym/availability/{machine}/{machine_number}",
            "bt": 0,
            "n": machine,
            "u": "binary",
            "v": value
        }

        data = {
            "device_id": f"simulated_{machine}_{machine_number}",
            "event_type": "availability",
            "type": record["n"],
            "location": self.location,
            "status": "active" if value == 1 else "inactive",
            "endpoint": record["bn"],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "senml_record": record
        }

        return data

    def simulate_usage(self, machine_type, machines_per_type, seconds=0):
        """Simulate usage for a specified type of machines ('cardio' or 'lifting') with a given number of machines per type."""
        # Select machines based on the machine type
        if machine_type == "cardio":
            machine_list = self.cardio_machines
        elif machine_type == "lifting":
            machine_list = self.lifting_machines
        else:
            raise ValueError("Invalid machine type. Choose 'cardio' or 'lifting'.")

        # Create a list of all machines with indices for the specified number of machines per type
        all_machines = [(machine, index) for machine in machine_list for index in range(1, machines_per_type + 1)]

        end_time = time.time() + seconds if seconds > 0 else time.time() + 1
        events = []

        while time.time() < end_time:
            # Shuffle the list of machines to simulate in a random order
            random.shuffle(all_machines)

            for machine, machine_index in all_machines:
                # Randomly simulate occupancy (1 = occupied, 0 = available)
                simulated_value = random.choice([0, 1])

                # Generate SenML formatted data for the current machine
                event = self.generate_sensor_data(simulated_value, machine, machine_index)
                events.append(event)

                # If only one data point is required, return immediately
                if seconds == 0:
                    return events

                # Wait a random interval between state changes
                time.sleep(random.randint(10, 20))

        return events

# Main section to demonstrate usage of SimulatedPIRSensor class
if __name__ == "__main__":
    try:
        # Ask user for the location of the simulation
        location = input("Enter the location for the simulation: ").strip()

        # Create the sensor with the specified location
        sensor = SimulatedPIRSensor(location=location)

        # Ask user for the duration of the simulation in seconds
        simulation_time = int(input("Enter the duration in seconds for simulation (0 for a single event): "))

        # Ask user to specify the type of machine to simulate
        machine_type = input("Enter the machine type to simulate ('cardio' or 'lifting'): ").strip().lower()

        # Ask user for the number of machines per type to simulate
        machines_per_type = int(input("Enter the number of machines per type to simulate: "))

        # Generate and print simulated data for the selected machine type and number of machines per type
        print(f"Simulated Data for {machine_type.capitalize()} Machines in {location}:")
        events = sensor.simulate_usage(machine_type=machine_type, machines_per_type=machines_per_type, seconds=simulation_time)
        for event in events:
            print(event)

    except ValueError as ve:
        print(f"Invalid input: {ve}")
    except KeyboardInterrupt:
        print("Simulation interrupted by user.")
