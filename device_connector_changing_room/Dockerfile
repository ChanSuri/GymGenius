FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install cherrypy requests paho-mqtt

EXPOSE 8093

CMD ["python", "device_connector_changing_room.py"]
