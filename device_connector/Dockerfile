FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install cherrypy requests

EXPOSE 8082

CMD ["python", "device_connector.py"]
