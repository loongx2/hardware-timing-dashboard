#!/bin/zsh

# Build and run the Docker container with compatibility settings

echo "🐳 Building and running Hardware Timing Dashboard"
echo "=============================================="

# Stop any existing containers
docker stop dashboard-container 2>/dev/null || true
docker rm dashboard-container 2>/dev/null || true

# Build the Docker image
echo "🔨 Building Docker image with Python 3.8..."
docker build -t dashboard:compat -f Dockerfile.compat .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    
    # Run the container
    echo "🚀 Starting container on http://localhost:8050"
    echo "Press Ctrl+C to stop"
    docker run --name dashboard-container -p 8050:8050 dashboard:compat
else
    echo "❌ Build failed. Trying local Python installation..."
    ./run_local.sh
fi
