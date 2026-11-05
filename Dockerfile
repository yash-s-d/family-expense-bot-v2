FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=True
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Google Cloud Run injects the PORT environment variable (default 8080)
ENV PORT=8080
EXPOSE 8080

# Run with Gunicorn using Cloud Run recommended configuration
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 webhook_server:app
