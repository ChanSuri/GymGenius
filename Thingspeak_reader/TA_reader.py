import requests
import pandas as pd
from io import StringIO
import json
import cherrypy
import os
import signal
import threading
import time
from registration_functions import *

# Load configuration for ThingSpeak
# with open('C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\Thingspeak_reader\\config_thingspeak.json') as f:
with open('config_thingspeak.json') as f:   
    thingspeak_config = json.load(f)

# Load configuration for service registration
# with open('C:\\Users\\feder\\OneDrive\\Desktop\\GymGenius\\Thingspeak_reader\\config_thingspeak_reader.json') as f:
with open('config_thingspeak_reader.json') as f:
    service_config = json.load(f)

THINGSPEAK_URL = thingspeak_config['ThingspeakURL_read']
CHANNELS = thingspeak_config['channels']

class ThingspeakAdaptor:
    exposed = True  # Make this CherryPy class accessible via HTTP

    def __init__(self, thingspeak_config, service_config, update_interval=30):
        """
        Initialize the ThingSpeak Adaptor with channel info from config.
        Also starts a thread to periodically update CSV files.
        :param update_interval: Time in seconds between updates (default: 300s = 5 minutes)
        """
        self.thingspeak_config = thingspeak_config
        self.service_config = service_config
        self.channels = CHANNELS
        self.update_interval = update_interval

        # Start the periodic update thread
        self.update_thread = threading.Thread(target=self.update_csv_periodically, daemon=True)
        self.update_thread.start()

    def update_csv_periodically(self):
        """Periodically updates CSV files with new data from ThingSpeak."""
        while True:
            print("Updating CSV files...")
            self.read_all_channels()
            print(f"CSV files updated! Next update in {self.update_interval} seconds.")
            time.sleep(self.update_interval)  # Wait before the next update

    def readCSV(self, channel_name, read_api_key, channel_id, fields):
        """Retrieve CSV data from ThingSpeak and structure it based on defined fields."""
        url = f"{THINGSPEAK_URL}{channel_id}/feeds.csv?api_key={read_api_key}&results=5000"
        
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            columns_to_keep = ['created_at', 'entry_id'] + [f'field{num}' for num in fields.values()]
            df = df[columns_to_keep]
            df.columns = ['created_at', 'entry_id'] + list(fields.keys())
            print(f"Data successfully retrieved from ThingSpeak for {channel_name}!")
            return df
        else:
            print(f"Failed to retrieve data from ThingSpeak for {channel_name}. Status: {response.status_code}")
            return None

    def read_all_channels(self):
        """Read data from all configured channels and save them as CSV."""
        saved_files = []
        for channel_name, channel_info in self.channels.items():
            df = self.readCSV(channel_name, channel_info['read_api_key'], channel_info['channel_id'], channel_info['fields'])
            if df is not None:
                file_name = f"thingspeak_data_{channel_name.replace(' ', '_')}.csv"
                df.to_csv(file_name, index=False)
                print(f"Data for {channel_name} saved as {file_name}")
                saved_files.append(file_name)
        return saved_files

    def GET(self, *uri, **params):
        """Serve the CSV file for the requested channel."""
        channel = params.get('channel')
        if not channel:
            cherrypy.response.status = 400
            return "Error: 'channel' parameter is required."

        file_name = f"thingspeak_data_{channel.replace(' ', '_')}.csv"
        if os.path.exists(file_name):
            cherrypy.response.headers['Content-Type'] = 'text/csv'
            cherrypy.response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
            with open(file_name, 'r') as f:
                return f.read()
        else:
            print(f"CSV file '{file_name}' not found.")
            cherrypy.response.status = 404
            return f"Error: CSV file for channel '{channel}' not found. Please ensure data fetching has run."

# Service initialization and signal handling
def initialize_service(service_config):
    """Register the service at startup."""
    register_service(service_config, service_config['service_catalog'])
    print("Thingspeak Adaptor Reader Service Initialized and Registered")

def stop_service(signum, frame):
    """Unregister and stop the service."""
    print("Stopping service...")
    delete_service("thingspeak_reader", service_config['service_catalog'])
    cherrypy.engine.exit()

if __name__ == "__main__":
    # Create the ThingspeakAdaptor instance
    TS = ThingspeakAdaptor(thingspeak_config, service_config)

    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True
        }
    }

    # Initialize service
    initialize_service(service_config)

    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, stop_service)
    signal.signal(signal.SIGTERM, stop_service)

    # Configure and start CherryPy server
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',  # Listen on all interfaces
        'server.socket_port': 8089,       # Listen on port 8089
    })
    # Mount the ThingspeakAdaptor class using MethodDispatcher
    cherrypy.tree.mount(TS, '/', conf)
    
    # Start the CherryPy server
    cherrypy.engine.start()
    cherrypy.engine.block()



