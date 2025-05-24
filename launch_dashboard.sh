#!/bin/zsh
# Universal launcher for Hardware Timing Dashboard
# This is a simple wrapper that calls the Python script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${(%):-%x}" )" &> /dev/null && pwd )"
if [ -z "$SCRIPT_DIR" ]; then
  SCRIPT_DIR=$(dirname "$0")
fi

# Navigate to the script directory
cd "$SCRIPT_DIR" || exit 1

# Execute the Python launcher
python3 dashboard.py
