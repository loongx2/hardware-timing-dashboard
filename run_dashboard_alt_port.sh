#!/bin/zsh
# run_dashboard_alt_port.sh - Run the dashboard with an alternative port mapping

echo "🐳 Running Hardware Timing Analytics Dashboard with alternative port"
echo "=================================================================="
echo "This script will run the dashboard on port 8051 instead of 8050"
echo "to avoid conflicts with existing services."

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ -z "$SCRIPT_DIR" ]; then
  SCRIPT_DIR=$(dirname "$0")
fi

# Navigate to the script directory
cd "$SCRIPT_DIR" || exit 1

# Check if docker is installed
if ! command -v docker &> /dev/null; then
  echo "❌ Error: Docker is not installed. Please install Docker to continue."
  exit 1
fi

# Ensure sample data is available
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

# Create data directory if it doesn't exist
mkdir -p data
if [ ! -s "data/sample_timing_data.csv" ]; then
  cp sample_timing_data.csv data/
  echo "✅ Sample data copied to data directory"
fi

# Run the dashboard with alternative port
echo "🚀 Starting dashboard with Docker on port 8051..."
docker run --rm -p 8051:8050 -v "$(pwd)/data:/app/data" dashboard:latest

echo "✅ Dashboard container stopped."
