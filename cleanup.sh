#!/bin/zsh
# Cleanup script to remove redundant launcher files

echo "🧹 Cleaning up redundant launcher files..."

# List of redundant files to remove
REDUNDANT_FILES=(
  "launch.py"
  "launch.sh"
  "launch.bat"
  "run.sh"
  "quick_launch.sh"
  "run_docker.sh"
  "run_local.sh"
  "run_compat.sh"
  "run_dashboard_alt_port.sh"
)

# Remove each file if it exists
for file in "${REDUNDANT_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo "Removing $file"
    rm "$file"
  fi
done

echo "✅ Cleanup complete!"
echo "🚀 The dashboard can now be launched with:"
echo "   - On macOS/Linux: ./launch_dashboard.sh"
echo "   - On Windows: launch_dashboard.bat"
