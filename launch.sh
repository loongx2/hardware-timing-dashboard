#!/bin/bash

# Hardware # Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create sample data directory if it doesn't exist
mkdir -p data

# Create a sample CSV file if it doesn't exist
if [ ! -f "data/sample_timing_data.csv" ]; then
    echo "📄 Creating sample CSV file..."
    cat > data/sample_timing_data.csv << EOF
Event,Time,Toggled
GPIO_Init,1000,True
GPIO_Init,1500,False
ADC_Read,2000,True
ADC_Read,4000,False
UART_Send,5000,True
UART_Send,13000,False
Timer_ISR,14000,True
Timer_ISR,15200,False
SPI_Transfer,16000,True
SPI_Transfer,19000,False
GPIO_Init,20000,True
GPIO_Init,20600,False
ADC_Read,21000,True
ADC_Read,23200,False
EOF
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting dashboard server..."
echo "📊 Dashboard will be available at: http://localhost:8050"
echo "📁 Sample CSV file available at: data/sample_timing_data.csv"
echo ""
echo "Expected CSV format:"
echo "  - Event: Name of the hardware event"
echo "  - Time: Timestamp in nanoseconds"
echo "  - Toggled: True when event starts, False when event ends"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""oard Launch Script
# This script sets up and launches the dashboard application

set -e  # Exit on any error

echo "🚀 Hardware Timing Analytics Dashboard Setup"
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting dashboard server..."
echo "📊 Dashboard will be available at: http://localhost:8050"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Launch the application
python app.py
