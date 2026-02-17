# Stage 1: Build dependencies
FROM python:3.12-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/install/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Install runtime dependencies (libpq)
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN addgroup --system appgroup && adduser --system --group appuser
USER appuser

# Copy installed packages from builder
COPY --from=builder /install /install

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
