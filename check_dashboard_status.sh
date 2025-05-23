#!/bin/zsh
# check_dashboard_status.sh - Check dashboard container status and health

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
if [ -z "$SCRIPT_DIR" ]; then
  SCRIPT_DIR=$(dirname "$0")
fi

# Navigate to the script directory
cd "$SCRIPT_DIR" || exit 1

echo "🔍 Checking Hardware Timing Analytics Dashboard status"
echo "===================================================="

# Check for running dashboard containers
echo "📊 Looking for dashboard containers..."
CONTAINERS=$(docker ps --filter "name=dashboard" --format "{{.ID}}\t{{.Names}}\t{{.Ports}}\t{{.Status}}")

if [ -z "$CONTAINERS" ]; then
  echo "❌ No dashboard containers found running."
  echo "   Try starting the dashboard with:"
  echo "   - docker compose up"
  echo "   - ./run_dashboard_alt_port.sh"
  exit 1
fi

echo "✅ Found running dashboard containers:"
echo "$CONTAINERS" | while read -r container; do
  echo "$container"
done

# Check container health
echo -e "\n🩺 Checking container health..."
IDS=$(docker ps --filter "name=dashboard" --format "{{.ID}}")

echo "$IDS" | while read -r id; do
  NAME=$(docker inspect --format='{{.Name}}' "$id" | sed 's/\///')
  HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}Not available{{end}}' "$id")
  
  echo "Container '$NAME' (ID: $id)"
  echo "Health status: $HEALTH"
  
  # If health is available, show last health check
  if [ "$HEALTH" != "Not available" ]; then
    LOG=$(docker inspect --format='{{if .State.Health}}{{range $i, $entry := .State.Health.Log}}{{if eq $i 0}}{{$entry.Output}}{{end}}{{end}}{{end}}' "$id")
    echo -e "Last health check output:"
    echo "$LOG" | head -n 10
  fi
  
  # Get exposed ports
  PORTS=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{if $conf}}{{range $conf}}{{$p}} -> {{.HostIp}}:{{.HostPort}}{{end}}{{end}}{{end}}' "$id")
  echo -e "Exposed ports:"
  echo "$PORTS"
  
  # Container metrics
  echo -e "Container metrics:"
  docker stats "$id" --no-stream --format "CPU: {{.CPUPerc}}, Memory: {{.MemUsage}}, Network I/O: {{.NetIO}}"
  echo -e "---------------------------------------"
done

echo -e "\n✅ Dashboard status check complete"
