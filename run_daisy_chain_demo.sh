#!/bin/zsh
# run_daisy_chain_demo.sh - Launch the dashboard with daisy chain sample data

echo "🔄 Starting Hardware Timing Analytics Dashboard with Daisy Chain Demo"
echo "=================================================================="

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ -z "$SCRIPT_DIR" ]; then
  SCRIPT_DIR=$(dirname "$0")
fi

# Navigate to the script directory
cd "$SCRIPT_DIR" || exit 1

# Ensure the data directory exists
mkdir -p data

# Check if the sample data exists
if [ ! -s "data/sample_data.csv" ]; then
  echo "❌ Sample data not found. Please make sure data/sample_data.csv exists."
  exit 1
fi

# Copy the sample data to the root directory for demonstration
cp data/sample_data.csv sample_timing_data.csv
echo "✅ Using sample data for demonstration"

# Check if we're in a Python virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
  echo "🐍 No active virtual environment detected"
  
  # Try to activate the virtual environment if it exists
  if [ -d "venv_new" ]; then
    echo "🐍 Activating virtual environment (venv_new)"
    source venv_new/bin/activate
  elif [ -d "venv" ]; then
    echo "🐍 Activating virtual environment (venv)"
    source venv/bin/activate
  else
    echo "⚠️ No virtual environment found. Consider creating one with:"
    echo "python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    echo "🔄 Continuing with system Python..."
  fi
fi

# Check if required packages are installed
if ! python3 -c "import dash" 2>/dev/null; then
  echo "📦 Installing required packages..."
  pip install -r requirements.txt
fi

# Start the dashboard
echo "🚀 Starting the dashboard..."
echo "📊 Dashboard will be available at http://localhost:8050"
echo "📋 Using daisy chain data: data/daisy_chain_sample.csv"
echo "------------------------------------------------------------"
python3 app.py

# If we activated a virtual environment, deactivate it
if [[ -n "$VIRTUAL_ENV" ]]; then
  deactivate
fi
