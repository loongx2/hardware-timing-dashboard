#!/bin/bash

# Hardware Timing Dashboard Launcher
echo "🚀 Launching Hardware Timing Dashboard..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if required dependencies are installed
python -c "import dash, pandas, plotly" 2>/dev/null || {
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements-py313.txt
}

# Launch the dashboard
echo "🌐 Starting dashboard on http://localhost:8050"
python app.py
