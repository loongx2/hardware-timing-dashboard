# Docker Deployment Guide

This guide provides detailed instructions for deploying the Hardware Timing Analytics Dashboard using Docker.

## Prerequisites

- Docker installed on your system
- Basic knowledge of terminal/command line
- Access to the dashboard source code

## Deployment Steps

### 1. Standard Deployment

```bash
# Navigate to the dashboard directory
cd /path/to/dashboard

# Build and run with Docker Compose
docker compose up --build
```

This will:
- Build a Docker image with all required dependencies
- Start a container that runs the dashboard application
- Make the dashboard accessible at http://localhost:8050

### 2. Alternative Port Deployment

If port 8050 is already in use on your system, you can modify the port mapping:

```bash
# Edit docker-compose.yml to change the port mapping
# From:
#   ports:
#     - "8050:8050"
# To:
#   ports:
#     - "8051:8050"

# Then run with the modified configuration
docker compose up
```

The dashboard will now be accessible at http://localhost:8051.

### 3. Manual Docker Deployment

You can also build and run the container manually:

```bash
# Build the Docker image
docker build -t dashboard:latest .

# Run the container
docker run -p 8050:8050 dashboard:latest

# Or with an alternative port
docker run -p 8051:8050 dashboard:latest
```

## Troubleshooting

### Port Conflicts

**Problem**: Error message about port already in use
```
Error response from daemon: failed to set up container networking: driver failed programming external connectivity on endpoint dashboard-dashboard-1: Bind for 0.0.0.0:8050 failed: port is already allocated
```

**Solution**:
1. Check for other containers using the port:
   ```bash
   docker ps | grep 8050
   ```
2. Either stop the conflicting container or use a different port:
   ```bash
   # Option 1: Stop conflicting container
   docker stop container_name
   
   # Option 2: Use different port in docker-compose.yml
   ports:
     - "8051:8050"
   ```

### Health Check Issues

The dashboard includes a health check configuration that verifies the application is running correctly:

```
Test: ["CMD", "curl", "-f", "http://localhost:8050/"]
```

If health checks are failing:
1. Check container logs: `docker logs <container_id>`
2. Verify the dashboard code is functioning correctly
3. Ensure sample data is available in the expected location

## Viewing Dashboard

After successful deployment, the dashboard provides:

1. **Key Statistics**:
   - Total Events
   - Average Execution Time
   - Fastest Event
   - Slowest Event

2. **Interactive Visualizations**:
   - Execution Time Comparison 
   - Event Distribution
   - Execution Time Trends
   - Execution Time Distribution
   - Detailed Timing Analysis

## Data Management

The dashboard can use:
1. Sample data included in the container
2. Custom data uploaded through the UI
3. Data mounted via Docker volumes

## Stopping the Container

To stop the running dashboard:

```bash
# If started with docker compose
docker compose down

# If started manually
docker stop <container_id>
```
