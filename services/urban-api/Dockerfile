FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY shared/ /app/shared/

# Create services package
RUN mkdir -p /app/services && touch /app/services/__init__.py

# Copy service code
COPY services/urban-api/ /app/services/urban-api/

# Install dependencies
COPY services/urban-api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Create data directory (mounted volume)
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "services.urban-api.main:app", "--host", "0.0.0.0", "--port", "8000"]
