FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install cherrypy pandas requests paho-mqtt

EXPOSE 8080

CMD ["python", "TA_reader.py"]
