FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install cherrypy requests paho-mqtt

EXPOSE 8092

CMD ["python", "device_connector_2.py"]
