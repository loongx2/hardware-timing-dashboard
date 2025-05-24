# Use Python 3.9 slim image for better compatibility
FROM python:3.9-slim

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
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure sample data directory exists
RUN mkdir -p /app/data

# Make sure sample data is properly copied (this ensures it's not empty)
RUN if [ -s /app/data/sample_timing_data.csv ]; then echo "Sample data exists"; else cp /app/sample_timing_data.csv /app/data/ || echo "No sample data found"; fi

# Make sure sample data is copied if it exists (with new name)
RUN if [ -s /app/data/sample_data.csv ]; then echo "Sample data exists"; else if [ -s /app/sample_data.csv ]; then cp /app/sample_data.csv /app/data/; fi; fi

# For backward compatibility, ensure daisy_chain_sample.csv is copied if it exists
RUN if [ -s /app/data/daisy_chain_sample.csv ]; then echo "Legacy sample data exists"; else if [ -s /app/daisy_chain_sample.csv ]; then cp /app/daisy_chain_sample.csv /app/data/; fi; fi

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
