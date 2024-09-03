FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install requests

EXPOSE 8082

CMD ["python", "simulate_button.py"]
