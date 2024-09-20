FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install paho-mqtt numpy pandas scikit-learn requests

CMD ["python", "occupancy.py"]
