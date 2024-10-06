import requests
import pandas as pd
from io import StringIO
import json
import cherrypy
import os

# Load configuration from config_thingspeak.json
with open('config_thingspeak.json') as f:
    config = json.load(f)

THINGSPEAK_URL = config['ThingspeakURL_read']
CHANNELS = config['channels']

class ThingspeakAdaptor:
    def __init__(self):
        """Initialize the ThingSpeak Adaptor with channel info from config."""
        self.channels = CHANNELS

    def readCSV(self, channel_name, read_api_key, channel_id, fields):
        """Read data in CSV format from ThingSpeak and structure it based on fields."""
        url = f"{THINGSPEAK_URL}{channel_id}/feeds.csv?api_key={read_api_key}&results=5000"
        
        # HTTP request to get CSV data from ThingSpeak
        response = requests.get(url)
        if response.status_code == 200:
            csv_data = response.text
            df = pd.read_csv(StringIO(csv_data))

            # Structure the DataFrame based on the required fields
            columns_to_keep = ['created_at', 'entry_id']
            for field_name, field_number in fields.items():
                columns_to_keep.append(f'field{field_number}')

            df = df[columns_to_keep]  # Keep only relevant columns
            df.columns = ['created_at', 'entry_id'] + list(fields.keys())  # Rename columns to actual field names

            print(f"Data successfully retrieved from ThingSpeak for {channel_name}!")
            return df
        else:
            print(f"Failed to retrieve data from ThingSpeak for {channel_name}. Status code: {response.status_code}")
            return None

    def read_all_channels(self):
        """Read data from all configured channels and save them as CSV."""
        saved_files = []
        for channel_name, channel_info in self.channels.items():
            read_api_key = channel_info['read_api_key']
            channel_id = channel_info['channel_id']
            fields = channel_info['fields']
            
            # Read CSV data for the channel
            df = self.readCSV(channel_name, read_api_key, channel_id, fields)
            if df is not None:
                # Save each DataFrame as a CSV file
                file_name = f"thingspeak_data_{channel_name.replace(' ', '_')}.csv"
                df.to_csv(file_name, index=False)
                print(f"Data for {channel_name} saved as {file_name}")
                saved_files.append(file_name)
        return saved_files

    @cherrypy.expose
    def thingspeak_adaptor(self, channel=None):
        """Serve a CSV file for the requested channel."""
        if not channel:
            cherrypy.response.status = 400
            return "Error: 'channel' parameter is required in the query string."

        # Check if the CSV file for the requested channel exists
        file_name = f"thingspeak_data_{channel.replace(' ', '_')}.csv"
        if os.path.exists(file_name):
            # Serve the file
            cherrypy.response.headers['Content-Type'] = 'text/csv'
            cherrypy.response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
            
            with open(file_name, 'r') as f:
                return f.read()
        else:
            # Log error in the terminal
            print(f"CSV file '{file_name}' not found.")
            cherrypy.response.status = 404
            return f"Error: CSV file for channel '{channel}' not found. Please make sure to run the data fetching process first."

if __name__ == "__main__":
    # Create the ThingspeakAdaptor instance
    TS = ThingspeakAdaptor()

    # Fetch data from ThingSpeak and save as CSV
    TS.read_all_channels()

    # Configure and start CherryPy server
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',  # Listen on all interfaces
        'server.socket_port': 8089,       # Listen on port 8080
    })

    # Start CherryPy and map the thingspeak_adaptor method to '/thingspeak_adaptor'
    cherrypy.quickstart(TS, '/thingspeak_adaptor/')


