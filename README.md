# Hardware Timing Analytics Dashboard

A Python-based dashboard built with Dash, Plotly, and Seaborn for analyzing embedded system hardware timing data from CSV files. Special focus on daisy chain configurations and synchronicity between devices.

## Features

- ⚡ **Execution Time Analysis**: Compare execution times across different hardware events
- 📊 **Interactive Visualizations**: Bar charts, pie charts, line plots, histograms, and box plots
- 📁 **CSV File Upload**: Drag-and-drop interface for uploading timing data
- 🔍 **Detailed Timing Analysis**: Statistical analysis with mean, std dev, min/max execution times
- 📈 **Trend Analysis**: Track execution time patterns over multiple runs
- 🎯 **Event Distribution**: Visualize frequency of different hardware events
- 🔌 **Device Topology Analysis**: Visualize and analyze daisy-chained embedded devices
- ⏱️ **Synchronicity Analysis**: Measure timing synchronization between multiple devices
- 🔄 **Communication Time Analysis**: Track message propagation through device chains

## Recent Improvements

- **Enhanced Daisy Chain Visualization**: Improved device topology visualization with correct positioning and connections
- **Improved Synchronicity Analysis**: Added detailed statistics for synchronization events between devices
- **Comprehensive Error Handling**: Better error handling for CSV file processing and data visualization
- **Advanced Visualization Options**: Added standard deviation visualizations and enhanced error bars
- **Robust Deployment Options**: Multiple ways to deploy including VS Code tasks, Docker, and local Python
- **Fixed Data Processing**: Enhanced CSV file processing to handle comment lines and formatting issues
## CSV Data Format

The dashboard supports two CSV formats:

### Basic Format (Single Device):

| Column   | Description                                    | Example    |
|----------|------------------------------------------------|------------|
| Event    | Name of the hardware event                     | GPIO_Init  |
| Time     | Timestamp in nanoseconds                       | 1000       |
| Toggled  | True when event starts, False when event ends | True/False |

### Extended Format (Multiple Devices):

| Column     | Description                                          | Example     |
|------------|------------------------------------------------------|-------------|
| Event      | Name of the hardware event                           | GPIO_Init   |
| Time       | Timestamp in nanoseconds                             | 1000        |
| Toggled    | True when event starts, False when event ends        | True/False  |
| Device_ID  | Identifier for the specific device                   | Device_1    |
| Position   | Position in the daisy chain (1=first, n=last)        | 1           |
| Message_ID | Identifier for tracking messages between devices     | MSG_12345   |

### Comment Lines in CSV:
The dashboard now supports comment lines in CSV files that start with `//` or `#`.

Example:
```csv
// This is a comment line that will be skipped during processing
# This is another comment line that will be skipped
Event,Time,Toggled,Device_ID,Position,Message_ID
GPIO_Init,1000,True,Device_1,1,
```

### Sample CSV (Basic):
GPIO_Init,1000,True
GPIO_Init,1500,False
ADC_Read,2000,True
ADC_Read,4000,False
UART_Send,5000,True
UART_Send,13000,False
```

### Sample Daisy Chain CSV:
```csv
Event,Time,Toggled,Device_ID,Position,Message_ID
GPIO_Init,1000,True,Device_1,1,
GPIO_Init,1500,False,Device_1,1,
UART_Send,15000,True,Device_1,1,MSG_12345
UART_Send,23000,False,Device_1,1,MSG_12345
UART_Receive,25000,True,Device_2,2,MSG_12345
UART_Receive,25500,False,Device_2,2,MSG_12345
```

### Synchronicity Events CSV Format:
For accurate synchronicity analysis, include Sync_Pulse events with SYNC_* Message_IDs:

```csv
Event,Time,Toggled,Device_ID,Position,Message_ID
Sync_Pulse,70000,True,Device_1,1,SYNC_1
Sync_Pulse,70300,False,Device_1,1,SYNC_1
Sync_Pulse,70050,True,Device_2,2,SYNC_1
Sync_Pulse,70350,False,Device_2,2,SYNC_1
Sync_Pulse,70100,True,Device_3,3,SYNC_1
Sync_Pulse,70400,False,Device_3,3,SYNC_1
```

### Data Files
The dashboard comes with several sample data files:
- `data/daisy_chain_truly_fixed.csv` - Properly formatted daisy chain data with synchronization events
- `data/sample_timing_data.csv` - Basic timing data for a single device
- `data/sample_data.csv` - Additional sample data for testing

**Important**: CSV files can now include comment lines starting with `//` or `#` - these will be automatically filtered during processing.

## Quick Start

### Option 1: Using VS Code Tasks (Recommended)

1. **Open the project in VS Code:**
   ```bash
   code /path/to/dashboard
   ```

2. **Run the Docker Build and Run task:**
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS)
   - Type "Tasks: Run Task" and select it
   - Choose "docker-run: debug"

3. **Access the dashboard:**
   ```
   http://localhost:8050
   ```

### Option 2: Using Launch Script

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

### Option 3: Manual Setup with Virtual Environment

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv_new
   source venv_new/bin/activate  # On macOS/Linux
   # venv_new\Scripts\activate   # On Windows
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

### Option 4: Docker Deployment

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

## Getting Started

The dashboard now comes with a simple, universal launcher that works on Windows, macOS, and Linux. The application always runs in Docker, ensuring consistent behavior across all platforms.

### Prerequisites

- Docker installed and running on your system
- Python 3.6+ installed on your system

### Running the Dashboard

1. Clone or download this repository
2. Run the dashboard using one of these methods:

#### On Windows:
```
launch_dashboard.bat
```

#### On macOS/Linux:
```
./launch_dashboard.sh
```

This will:
1. Build the Docker image if it doesn't exist
2. Start a Docker container with the dashboard
3. Make the dashboard accessible at http://localhost:8050
4. Open your default web browser to this URL

### No Command Line Options

The launcher now uses a fixed configuration:
- Always runs in Docker
- Always uses port 8050
- Always mounts the local data directory to the container

## Troubleshooting

### Common Issues and Solutions

#### Dashboard Not Loading in Browser
1. **Check if the application is running**:
   ```bash
   docker ps | grep dashboard
   # or if running locally
   ps aux | grep app.py
   ```

2. **Verify port availability**:
   ```bash
   lsof -i :8050
   ```
   If port 8050 is already in use, modify the port in app.py or use the Docker port mapping.

3. **Check application logs**:
   ```bash
   # For Docker:
   docker logs hardware-timing-dashboard
   
   # For local run:
   # Look at the terminal output where you launched the app
   ```

#### Syntax Errors in app.py
If you encounter syntax errors like "name assigned before global declaration" or other syntax issues:

1. Check the app.py file for misplaced code after `app.run_server()` call
2. Ensure all callback functions are properly structured with:
   - `@app.callback` decorator
   - Function definition with appropriate input/output parameters
   - Proper indentation

#### CSV File Loading Issues
1. **Verify CSV format**:
   - Comment lines starting with `//` or `#` are now supported
   - Check that column names match expected format (Event, Time, Toggled, etc.)
   - Verify data types (Time should be numeric, Toggled should be boolean)

2. **Fix CSV file format issues**:
   ```bash
   # If needed, you can manually fix problematic CSV files:
   sed 's/invalidFormat/correctFormat/g' problematic_file.csv > fixed_file.csv
   ```

#### Docker-related Issues
1. **Rebuild Docker image after changes**:
   ```bash
   docker-compose build --no-cache
   ```

2. **Check Docker logs**:
   ```bash
   docker-compose logs
   ```

3. **Verify volume mounting**:
   If data files aren't being accessed correctly, check that volumes are properly mounted in docker-compose.yml

#### Virtual Environment Issues
1. **Use the correct virtual environment**:
   ```bash
   # Use venv_new instead of venv
   source venv_new/bin/activate
   ```

2. **Check installed packages**:
   ```bash
   pip list
   ```

3. **Reinstall dependencies if needed**:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

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
