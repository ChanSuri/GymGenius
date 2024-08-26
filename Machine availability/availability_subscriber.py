import json
import random
import time
import datetime
from MyMQTT import *

class DataCollector():
    """A class to collect and display data from MQTT topics in a user-friendly format."""

    def __init__(self, clientID, broker, baseTopic):
        self.clientID = clientID
        self.baseTopic = "GymGenius/" + baseTopic
        self.client = MyMQTT(clientID, broker, 1883, self)

    def run(self):
        """Starts the MQTT client."""
        self.client.start()
        print(f'{self.clientID} has started')

    def end(self):
        """Stops the MQTT client."""
        self.client.stop()
        print(f'{self.clientID} has stopped')

    def follow(self, topic):
        """Subscribes to a specific topic."""
        self.client.mySubscribe(topic)

    def notify(self, topic, msg):
        """
        Handles incoming messages by updating the 'availability' part of gymCatalog.json
        with the new message's information.
        """
        try:
            payload = json.loads(msg)
        except json.JSONDecodeError:
            print("Error decoding the message.")
            return
        
        try:
            data = self._read_json("gymCatalog.json")
        except FileNotFoundError:
            print("File gymCatalog.json not found.")
            return
        
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["lastUpdate"] = date_now

        room_id = payload["bn"].split("/")[2]
        machine_name = payload["bn"].split("/")[-1]

        for room in data.get("rooms", []):
            if room.get("roomID") == room_id:
                self._update_room_availability(room, machine_name, payload["v"])
                room["lastUpdate"] = date_now

        self._write_json("gymCatalog.json", data)

    def _update_room_availability(self, room, machine_name, value):
        """Updates the availability of a specific machine in a room."""
        for service in room.get("services", []):
            if "availability" in service:
                for sensor in service["availability"].get("data", []):
                    if sensor["machineName"] == machine_name:
                        sensor["value"] = value

    def _read_json(self, filepath):
        """Reads JSON data from a file."""
        with open(filepath, "r") as file:
            return json.load(file)

    def _write_json(self, filepath, data):
        """Writes JSON data to a file."""
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)

if __name__ == "__main__":
    conf = json.load(open("gymCatalog.json"))
    coll = DataCollector('dc' + str(random.randint(1, 10**5)), conf["broker"], baseTopic=conf["baseTopic"])
    coll.run()
    coll.follow(coll.baseTopic + '+/availability/#')
    try:
        print("Collecting data. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)  # Simple delay to keep the loop running
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        coll.end()
