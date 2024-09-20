FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install requests telepot cherrypy paho-mqtt

EXPOSE 8086

CMD ["python", "telegramBot.py"]
