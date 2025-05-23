#!/bin/zsh

# This script creates a local directory structure, copies the necessary files,
# and runs the dashboard in Python directly.

echo "🚀 Setting up local dashboard environment"
echo "========================================"

# Create a temporary directory for the application
TEMP_DIR="/tmp/dashboard_docker_app"
mkdir -p "$TEMP_DIR"

# Copy necessary files
echo "📋 Copying application files..."
cp -r /Volumes/KINGSTON/workspace/dashboard/app.py "$TEMP_DIR"
cp -r /Volumes/KINGSTON/workspace/dashboard/requirements.txt "$TEMP_DIR"
mkdir -p "$TEMP_DIR/data"
cp -r /Volumes/KINGSTON/workspace/dashboard/sample_timing_data.csv "$TEMP_DIR/data"

# Create a Python virtual environment
echo "🐍 Creating Python environment..."
cd "$TEMP_DIR"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Run the application
echo "🚀 Starting the dashboard..."
echo "The dashboard will be available at: http://localhost:8050"
python app.py
