FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src src

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
