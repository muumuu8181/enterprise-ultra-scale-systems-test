FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command
CMD ["celery", "-A", "src.worker.celery", "worker", "--loglevel=info"]
