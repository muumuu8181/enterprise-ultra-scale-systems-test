FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Copy service code
COPY services/traffic-collector/ /app/services/traffic-collector/

# Install dependencies
COPY services/traffic-collector/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set PYTHONPATH
ENV PYTHONPATH=/app

CMD ["python", "services/traffic-collector/main.py"]
