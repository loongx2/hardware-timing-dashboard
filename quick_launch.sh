#!/bin/zsh

# Launch Hardware Timing Dashboard
# This script provides a simple way to launch the dashboard

echo "🚀 Hardware Timing Dashboard Launcher"
echo "====================================="
echo "Attempting to launch the dashboard..."

# Try multiple methods until one works
(cd /Volumes/KINGSTON/workspace/dashboard && ./run_docker.sh) || \
(cd /Volumes/KINGSTON/workspace/dashboard && python app_standalone.py) || \
(cd /Volumes/KINGSTON/workspace/dashboard && ./run_local.sh) || \
(cd /Volumes/KINGSTON/workspace/dashboard && ./run_compat.sh) || \
echo "❌ All launch methods failed. Please check the error messages above."

# Open the browser automatically
sleep 2
open http://localhost:8050
