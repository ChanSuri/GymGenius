import requests
import pandas as pd
from io import StringIO
import json
import cherrypy

# Load configuration from config.json
with open('config.json') as f:
    config = json.load(f)

THINGSPEAK_URL = config['ThingspeakURL']
CHANNELS = config['channels']

class ThingspeakReader:
    def __init__(self):
        """Initialize the ThingSpeak reader with channel info from config."""
        self.channels = CHANNELS

    def readCSV(self, channel_name, read_api_key, channel_id):
        """Read data in CSV format from ThingSpeak."""
        # URL for reading data from ThingSpeak in CSV format
        url = f"{THINGSPEAK_URL}{channel_id}/feeds.csv?api_key={read_api_key}&results=5000"
        
        # HTTP request to get CSV data from ThingSpeak
        response = requests.get(url)

        if response.status_code == 200:
            csv_data = response.text
            df = pd.read_csv(StringIO(csv_data))
            print(f"Data successfully retrieved from ThingSpeak for {channel_name}!")

            # Return the DataFrame with the data
            return df
        else:
            print(f"Failed to retrieve data from ThingSpeak for {channel_name}. Status code: {response.status_code}")
            return None

    def save_csv_for_channel(self, channel_name):
        """Fetch data for the specific channel and save it as a CSV."""
        channel_info = self.channels.get(channel_name)

        if channel_info:
            read_api_key = channel_info['read_api_key']
            channel_id = channel_info['channel_id']
            
            # Read CSV data for the channel
            df = self.readCSV(channel_name, read_api_key, channel_id)

            if df is not None:
                # Save the DataFrame as a CSV file
                file_name = f"thingspeak_data_{channel_name.replace(' ', '_')}.csv"
                df.to_csv(file_name, index=False)
                print(f"Data for {channel_name} saved as {file_name}")
                return file_name
        else:
            print(f"Channel {channel_name} not found in the configuration.")
            return None

    @cherrypy.expose
    def GET(self, *uri, **params):
        """Handle GET requests to serve CSV files based on the requested channel."""
        # Check if 'channel' parameter is provided
        channel = params.get('channel')
        
        if not channel:
            # If the channel parameter is missing, return a 400 Bad Request response
            cherrypy.response.status = 400
            return "Error: 'channel' parameter is required in the query string."

        # Save CSV for the requested channel
        file_name = self.save_csv_for_channel(channel)
        
        if file_name:
            # Set response headers for a CSV file download
            cherrypy.response.headers['Content-Type'] = 'text/csv'
            cherrypy.response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
            
            # Read and return the contents of the CSV file
            with open(file_name, 'r') as f:
                return f.read()
        else:
            cherrypy.response.status = 404
            return f"Error: Channel '{channel}' not found or error retrieving data."

if __name__ == "__main__":
    # CherryPy configuration
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',  # Listen on all interfaces
        'server.socket_port': 8080,       # Listen on port 8080
    })

    # Start the CherryPy server
    cherrypy.quickstart(ThingspeakReader())
