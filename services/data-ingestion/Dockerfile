FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy service code
COPY services/data-ingestion/ /app/services/data-ingestion/

# Install dependencies
COPY services/data-ingestion/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Create data directory
RUN mkdir -p /app/data

CMD ["python", "services/data-ingestion/main.py"]
