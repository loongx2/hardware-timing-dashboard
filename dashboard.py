#!/usr/bin/env python3
"""
Universal launcher for Hardware Timing Analytics Dashboard
Works on Windows, macOS, and Linux - Always using Docker
"""

import os
import sys
import platform
import subprocess
import time
import webbrowser
from pathlib import Path

# Configuration
APP_NAME = "Hardware Timing Dashboard"
DOCKER_IMAGE = "dashboard:latest"
CONTAINER_NAME = "hardware-timing-dashboard"
PORT = 8050

def print_header():
    """Print the application header"""
    print("=" * 60)
    print(f"⚡ {APP_NAME} Launcher")
    print("=" * 60)

def is_docker_available():
    """Check if Docker is installed and available"""
    try:
        subprocess.run(["docker", "--version"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE,
                      check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def ensure_sample_data():
    """Ensure sample data files exist in the proper locations"""
    script_dir = Path(__file__).parent.absolute()
    data_dir = script_dir / "data"
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Check for sample data
    sample_data_dest = data_dir / "sample_data.csv"
    
    # Check for different possible source files
    possible_sources = [
        data_dir / "daisy_chain_sample.csv",
        script_dir / "sample_timing_data.csv",
        data_dir / "sample_timing_data.csv"
    ]
    
    source_file = None
    for src in possible_sources:
        if src.exists() and src.stat().st_size > 0:
            source_file = src
            break
    
    if source_file:
        # Copy to sample_data.csv if needed
        if not sample_data_dest.exists() or sample_data_dest.stat().st_size == 0:
            print(f"✅ Copying sample data from {source_file.name}")
            with open(source_file, 'r') as src_f:
                with open(sample_data_dest, 'w') as dest_f:
                    dest_f.write(src_f.read())
    else:
        # Create minimal sample data if none exists
        print("⚠️ No sample data found, creating minimal sample...")
        with open(sample_data_dest, 'w') as f:
            f.write("Event,Time,Toggled,Device_ID,Position,Message_ID\n")
            f.write("GPIO_Init,1000,True,Device_1,1,\n")
            f.write("GPIO_Init,1500,False,Device_1,1,\n")
            f.write("ADC_Read,2000,True,Device_1,1,\n")
            f.write("ADC_Read,4000,False,Device_1,1,\n")
    
    return sample_data_dest.exists()

def check_container_exists():
    """Check if the dashboard container already exists"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return CONTAINER_NAME in result.stdout
    except subprocess.SubprocessError:
        return False

def remove_container():
    """Remove the existing container if it exists"""
    if check_container_exists():
        print(f"🗑️ Removing existing container: {CONTAINER_NAME}")
        try:
            subprocess.run(["docker", "stop", CONTAINER_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["docker", "rm", CONTAINER_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.SubprocessError as e:
            print(f"⚠️ Error removing container: {e}")
            return False
    return True

def build_docker_image():
    """Build the Docker image for the dashboard"""
    global DOCKER_IMAGE
    
    print("🔨 Checking for Docker image...")
    script_dir = Path(__file__).parent.absolute()
    
    # Check if image already exists
    try:
        result = subprocess.run(
            ["docker", "images", "-q", DOCKER_IMAGE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            print("✅ Docker image already exists!")
            return True
    except subprocess.SubprocessError:
        pass
    
    # If no existing image, try dashboard-dashboard image (common name in docker-compose)
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "dashboard-dashboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            print("✅ Found dashboard-dashboard image!")
            # Set global variable to use this image instead
            DOCKER_IMAGE = "dashboard-dashboard"
            return True
    except subprocess.SubprocessError:
        pass
    
    # Try to build a new image
    print("🔨 Building new Docker image...")
    try:
        subprocess.run(
            ["docker", "build", "-t", DOCKER_IMAGE, "."],
            cwd=script_dir,
            check=True
        )
        print("✅ Docker image built successfully!")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Docker build failed: {e}")
        return False

def run_docker_container():
    """Run the Docker container with the dashboard"""
    print(f"🚀 Starting dashboard container on port {PORT}...")
    script_dir = Path(__file__).parent.absolute()
    data_dir = script_dir / "data"
    
    # Check if image exists first
    try:
        result = subprocess.run(
            ["docker", "images", "-q", DOCKER_IMAGE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        if not result.stdout.strip():
            print(f"❌ Docker image '{DOCKER_IMAGE}' not found.")
            return False
    except subprocess.SubprocessError:
        print("❌ Failed to check for Docker image.")
        return False
    
    # Try to run the container
    try:
        cmd = [
            "docker", "run",
            "--name", CONTAINER_NAME,
            "-p", f"{PORT}:8050",
            "-v", f"{data_dir.absolute()}:/app/data",
            "-d",  # Run in detached mode
            DOCKER_IMAGE
        ]
        subprocess.run(cmd, check=True)
        
        print(f"✅ Container started successfully!")
        print(f"📊 Dashboard is available at http://localhost:{PORT}")
        return True
    except subprocess.SubprocessError as e:
        print(f"❌ Failed to start container: {e}")
        
        # Try running without the volume mount as a fallback
        try:
            print("⚠️ Trying fallback method without volume mount...")
            cmd = [
                "docker", "run",
                "--name", CONTAINER_NAME,
                "-p", f"{PORT}:8050",
                "-d",  # Run in detached mode
                DOCKER_IMAGE
            ]
            subprocess.run(cmd, check=True)
            
            print(f"✅ Container started successfully (without data volume)!")
            print(f"📊 Dashboard is available at http://localhost:{PORT}")
            return True
        except subprocess.SubprocessError as e2:
            print(f"❌ Fallback also failed: {e2}")
            return False

def check_container_health():
    """Check if the container is healthy"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", CONTAINER_NAME],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            status = result.stdout.strip()
            
            if status == "healthy":
                return True
            elif status == "unhealthy":
                print("⚠️ Container is unhealthy!")
                return False
            else:
                print(f"⏳ Container status: {status} (attempt {attempt+1}/{max_attempts})")
                time.sleep(3)
        except subprocess.SubprocessError:
            print(f"⏳ Waiting for container to start (attempt {attempt+1}/{max_attempts})...")
            time.sleep(3)
    
    print("⚠️ Container health check timed out")
    return False

def open_dashboard_in_browser():
    """Open the dashboard in the default web browser"""
    dashboard_url = f"http://localhost:{PORT}"
    print(f"🌐 Opening dashboard in browser: {dashboard_url}")
    
    try:
        webbrowser.open(dashboard_url)
        return True
    except Exception as e:
        print(f"⚠️ Failed to open browser: {e}")
        print(f"Please manually open: {dashboard_url}")
        return False

def show_logs():
    """Show the logs from the dashboard container"""
    try:
        subprocess.run(["docker", "logs", "-f", CONTAINER_NAME])
    except KeyboardInterrupt:
        print("\n🛑 Stopped viewing logs")
    except subprocess.SubprocessError as e:
        print(f"⚠️ Error viewing logs: {e}")

def main():
    """Main function to run the dashboard"""
    print_header()
    
    # Check if Docker is available
    if not is_docker_available():
        print("❌ Docker is not available. Please install Docker to continue.")
        sys.exit(1)
    
    # Ensure sample data exists
    if not ensure_sample_data():
        print("⚠️ Failed to set up sample data")
    
    # Remove existing container if it exists
    if not remove_container():
        print("⚠️ Failed to remove existing container")
    
    # Build the Docker image
    if not build_docker_image():
        print("❌ Failed to build Docker image. Exiting.")
        sys.exit(1)
    
    # Run the Docker container
    if not run_docker_container():
        print("❌ Failed to run Docker container. Exiting.")
        sys.exit(1)
    
    # Check container health
    print("⏳ Waiting for container to be ready...")
    if check_container_health():
        print("✅ Container is healthy and ready!")
    else:
        print("⚠️ Container may not be fully operational")
    
    # Open the dashboard in the browser
    open_dashboard_in_browser()
    
    # Ask user if they want to see logs
    try:
        show_logs_input = input("\nDo you want to view container logs? (y/n): ")
        if show_logs_input.lower() == 'y':
            show_logs()
    except (KeyboardInterrupt, EOFError):
        pass
    
    print("\n✅ Launch complete!")
    print(f"📊 Dashboard is running at http://localhost:{PORT}")
    print("🛑 To stop the dashboard, run: docker stop " + CONTAINER_NAME)

if __name__ == "__main__":
    main()
