#!/bin/zsh

# This script builds and runs the dashboard in Docker without requiring Docker Hub credentials

echo "🐳 Building and running dashboard in Docker"
echo "========================================"

# Ensure the sample data is available
if [ ! -s "sample_timing_data.csv" ]; then
    echo "⚠️ Sample data file is empty or missing, attempting to fix..."
    if [ -s "data/sample_timing_data.csv" ]; then
        cp data/sample_timing_data.csv sample_timing_data.csv
        echo "✅ Sample data copied from data directory"
    else
        echo "❌ No sample data found in data directory"
        echo "Creating minimal sample data..."
        echo "Event,Time,Toggled
GPIO_Init,1000,True
GPIO_Init,1500,False
ADC_Read,2000,True
ADC_Read,4000,False" > sample_timing_data.csv
    fi
fi

# Build the Docker image locally
echo "🔨 Building Docker image..."
docker build -t dashboard:latest .

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    
    # Stop any existing container
    echo "🛑 Stopping existing containers..."
    docker stop dashboard-container 2>/dev/null || true
    docker rm dashboard-container 2>/dev/null || true
    
    # Run the Docker container
    echo "🚀 Starting dashboard container..."
    echo "📊 Dashboard will be available at: http://localhost:8050"
    docker run --name dashboard-container -p 8050:8050 dashboard:latest
else
    echo "❌ Docker build failed"
    exit 1
fi
