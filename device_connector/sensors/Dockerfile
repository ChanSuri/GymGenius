# Use a slim Python image as the base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy all files to the working directory in the container
COPY . .

# Install necessary dependencies (Test with raspberry)
# RUN apt-get update && apt-get install -y python3-rpi.gpio python3-pip libgpiod-dev \
#     && pip install adafruit-circuitpython-dht RPi.GPIO requests

# Test without raspberry
RUN pip install requests

# Define the default command (this will be overwritten for each container in docker-compose.yml)
CMD ["python", "simulate_button.py"]
