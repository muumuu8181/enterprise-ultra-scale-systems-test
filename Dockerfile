FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for psycopg2 if needed (slim might lack some build tools but binary usually works)
# But standard python images are fine.
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg2-binary redis celery

COPY src /app/src

CMD ["celery", "-A", "src.worker", "worker", "--loglevel=info"]
