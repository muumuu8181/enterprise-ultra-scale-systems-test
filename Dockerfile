FROM python:3.11-slim

WORKDIR /app

RUN pip install celery redis sqlalchemy fastapi uvicorn pydantic

COPY . .

CMD ["celery", "-A", "src.worker", "worker", "--loglevel=info"]
