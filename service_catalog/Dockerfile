# Usa un'immagine base di Python
FROM python:3.9-slim

# Imposta la directory di lavoro nel container
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia i file necessari nella directory di lavoro
COPY . .

# Espone la porta su cui gira il servizio
EXPOSE 8080

# Comando per avviare il server CherryPy
CMD ["python", "service_catalog.py"]