# Usa un'immagine base di Python
FROM python:3.9-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia i file necessari nella directory di lavoro
COPY . .

# Installa le dipendenze
RUN pip install cherrypy requests

# Espone la porta su cui gira il servizio
EXPOSE 8080

# Comando per avviare il server CherryPy
CMD ["python", "service_catalog.py"]