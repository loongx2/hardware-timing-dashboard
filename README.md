# Hardware Timing Analytics Dashboard

A Python-based dashboard built with Dash, Plotly, and Seaborn for analyzing embedded system hardware timing data from CSV files.

## Features

- ⚡ **Execution Time Analysis**: Compare execution times across different hardware events
- 📊 **Interactive Visualizations**: Bar charts, pie charts, line plots, histograms, and box plots
- 📁 **CSV File Upload**: Drag-and-drop interface for uploading timing data
- 🔍 **Detailed Timing Analysis**: Statistical analysis with mean, std dev, min/max execution times
- 📈 **Trend Analysis**: Track execution time patterns over multiple runs
- 🎯 **Event Distribution**: Visualize frequency of different hardware events
## CSV Data Format

The dashboard expects CSV files with the following columns:

| Column   | Description                                    | Example    |
|----------|------------------------------------------------|------------|
| Event    | Name of the hardware event                     | GPIO_Init  |
| Time     | Timestamp in nanoseconds                       | 1000       |
| Toggled  | True when event starts, False when event ends | True/False |

### Sample CSV:
```csv
Event,Time,Toggled
GPIO_Init,1000,True
GPIO_Init,1500,False
ADC_Read,2000,True
ADC_Read,4000,False
UART_Send,5000,True
UART_Send,13000,False
```

## Quick Start

### Option 1: Using Launch Script (Recommended)

1. **Make the launch script executable:**
   ```bash
   chmod +x launch.sh
   ```

2. **Run the launch script:**
   ```bash
   ./launch.sh
   ```

This will automatically:
- Create a virtual environment
- Install all dependencies
- Create sample data
- Launch the dashboard

### Option 2: Manual Setup with Virtual Environment

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # venv\Scripts\activate   # On Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser and navigate to:**
   ```
   http://localhost:8050
   ```

### Option 3: Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually:**
   ```bash
   docker build -t dashboard:latest .
   docker run -p 8050:8050 dashboard:latest
   ```

3. **If port 8050 is already in use, modify the port mapping:**
   ```bash
   # In docker-compose.yml:
   ports:
     - "8051:8050"  # Maps host port 8051 to container port 8050
   
   # Or with docker run command:
   docker run -p 8051:8050 dashboard:latest
   ```

4. **Access the dashboard:**
   ```
   http://localhost:8050  # Default port
   http://localhost:8051  # If using alternative port
   ```

## Project Structure

```
dashboard/
├── app.py                 # Main dashboard application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
└── README.md            # This file
```

## Dependencies

- **Dash**: Web application framework
- **Plotly**: Interactive plotting library
- **Seaborn**: Statistical data visualization
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **Bootstrap**: UI components

## Development

To modify the dashboard:

1. Edit `app.py` to add new visualizations or modify existing ones
2. Add new dependencies to `requirements.txt`
3. Test locally with `python app.py`
4. Rebuild Docker image if needed

## Production Deployment

For production deployment, consider:

- Using Gunicorn as WSGI server
- Setting up reverse proxy with Nginx
- Using environment variables for configuration
- Implementing proper logging and monitoring
