FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY nebula ./nebula
COPY imports ./imports

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose API port
EXPOSE 8000

# Run FastAPI application
CMD ["uvicorn", "nebula.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
