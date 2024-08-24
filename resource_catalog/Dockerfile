FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install cherrypy requests

EXPOSE 8081

CMD ["python", "resource_catalog.py"]
