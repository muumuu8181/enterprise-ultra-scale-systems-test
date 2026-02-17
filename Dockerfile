FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for shapely/geoalchemy2 (geos) and psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc python3-dev libgeos-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
