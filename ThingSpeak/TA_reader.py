import requests
import pandas as pd
from io import StringIO
import json

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

    def read_all_channels(self):
        """Read data from all configured channels and save it."""
        for channel_name, channel_info in self.channels.items():
            read_api_key = channel_info['read_api_key']
            channel_id = channel_info['channel_id']
            
            # Read CSV data for the channel
            df = self.readCSV(channel_name, read_api_key, channel_id)

            if df is not None:
                # Save each DataFrame as a CSV file
                file_name = f"thingspeak_data_{channel_name.replace(' ', '_')}.csv"
                df.to_csv(file_name, index=False)
                print(f"Data for {channel_name} saved as {file_name}")

if __name__ == "__main__":
    TS = ThingspeakReader()
    TS.read_all_channels()
