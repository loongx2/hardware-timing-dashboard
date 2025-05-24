# Use Python 3.12 for better compatibility with packages
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DASH_PORT=8050

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-py313.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure sample data directory exists and copy data
RUN mkdir -p /app/data
COPY data/ /app/data/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1

# Run the application
CMD ["python", "app.py"]
