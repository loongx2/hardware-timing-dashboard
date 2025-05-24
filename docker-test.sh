#!/bin/bash

# Dashboard Docker Test Script
# This script builds and runs the dashboard app in Docker

set -e

echo "🐳 Dashboard Docker Test Workflow"
echo "================================="

# Stop and remove existing container if it exists
echo "📦 Cleaning up existing containers..."
docker stop dashboard-simple 2>/dev/null || true
docker rm dashboard-simple 2>/dev/null || true

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -f Dockerfile.simple -t dashboard:simple .

# Run the container
echo "🚀 Starting container..."
docker run -d -p 8050:8050 --name dashboard-simple dashboard:simple

# Wait a moment for the app to start
echo "⏳ Waiting for app to start..."
sleep 3

# Check if container is running
if docker ps | grep -q dashboard-simple; then
    echo "✅ Container is running successfully!"
    echo "📱 Dashboard is available at: http://localhost:8050"
    echo ""
    echo "🔍 Container logs:"
    docker logs dashboard-simple
    echo ""
    echo "🛑 To stop the container, run: docker stop dashboard-simple"
else
    echo "❌ Container failed to start!"
    echo "🔍 Container logs:"
    docker logs dashboard-simple
    exit 1
fi
