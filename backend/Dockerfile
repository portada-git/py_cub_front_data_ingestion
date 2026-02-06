# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including Java for PySpark)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    default-jdk \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME for PySpark
ENV JAVA_HOME=/usr/lib/jvm/default-java

# Install UV using pip
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./
COPY .env ./
COPY main.py ./
COPY app/ ./app/

# Install Python dependencies
RUN uv sync --no-cache

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start the application
CMD ["uv", "run", "python", "main.py"]