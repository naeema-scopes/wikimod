FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY . .

# Make download script executable
RUN chmod +x scripts/download_model.sh

# Download model artifacts if not present, then start server
CMD ["sh", "-c", "scripts/download_model.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

EXPOSE 8000
