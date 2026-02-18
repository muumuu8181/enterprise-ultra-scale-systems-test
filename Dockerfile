FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src src

# Assuming the app will start with uvicorn
CMD ["uvicorn", "src.api.v1.websocket:app", "--host", "0.0.0.0", "--port", "8000"]
