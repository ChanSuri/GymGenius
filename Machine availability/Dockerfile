FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install paho-mqtt requests

CMD ["python", "machine_availability.py"]
