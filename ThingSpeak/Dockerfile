FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install cherrypy pandas requests paho-mqtt

CMD ["python", "TA.py"]
