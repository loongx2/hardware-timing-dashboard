#!/bin/bash
# filepath: /Volumes/KINGSTON/workspace/dashboard/docker_restart.sh

echo "🔄 Restarting Docker container for Hardware Timing Dashboard..."

# Stop and remove the current container
echo "🛑 Stopping current container..."
docker stop dashboard-simple

echo "🗑️ Removing container..."
docker rm dashboard-simple

# Rebuild the image with latest changes
echo "🏗️ Rebuilding Docker image..."
docker build -t dashboard:simple -f Dockerfile.simple .

# Start a fresh container
echo "🚀 Starting new container..."
docker run -d -p 8050:8050 --name dashboard-simple dashboard:simple

# Check if container started successfully
echo "✅ Checking container status..."
docker ps | grep dashboard-simple

echo "🌐 Dashboard should be available at http://localhost:8050"
echo "📊 To view logs: docker logs dashboard-simple"
