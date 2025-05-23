#!/bin/bash

# Build and save Docker image script for Hardware Timing Dashboard
# This script builds a Docker image and saves it to the specified location

# Set variables
IMAGE_NAME="hardware-timing-dashboard"
IMAGE_TAG="latest"
OUTPUT_DIR="/Volumes/KINGSTON/workspace/DockerDesktop/dashboard"

echo "🐳 Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "===================================================="

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    
    # Save the Docker image to a tar file
    echo "💾 Saving Docker image to: ${OUTPUT_DIR}/${IMAGE_NAME}.tar"
    docker save ${IMAGE_NAME}:${IMAGE_TAG} -o "${OUTPUT_DIR}/${IMAGE_NAME}.tar"
    
    if [ $? -eq 0 ]; then
        echo "✅ Docker image saved successfully to: ${OUTPUT_DIR}/${IMAGE_NAME}.tar"
        echo ""
        echo "🔍 Image details:"
        docker images ${IMAGE_NAME}:${IMAGE_TAG}
        echo ""
        echo "📋 To load this image on another machine:"
        echo "   docker load -i ${OUTPUT_DIR}/${IMAGE_NAME}.tar"
        echo ""
        echo "🚀 To run the container:"
        echo "   docker run -p 8050:8050 ${IMAGE_NAME}:${IMAGE_TAG}"
    else
        echo "❌ Failed to save Docker image"
    fi
else
    echo "❌ Docker build failed"
    exit 1
fi
