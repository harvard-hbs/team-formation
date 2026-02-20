#!/usr/bin/env bash
# Build the Python backend into a standalone bundle using PyInstaller.
#
# Usage:
#   cd desktop
#   ./scripts/build-python.sh
#
# Prerequisites:
#   pip install pyinstaller
#   pip install -e ..   (or ensure team_formation is importable)
#
# Output:
#   desktop/python-dist/  (the bundled backend ready for Electron packaging)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$(cd "$DESKTOP_DIR/.." && pwd)"

echo "=== Building Python backend ==="
echo "Project root: $PROJECT_DIR"
echo "Desktop dir:  $DESKTOP_DIR"

# Ensure we're in the desktop directory for spec file paths
cd "$DESKTOP_DIR"

# Clean previous build
rm -rf build dist python-dist

# Run PyInstaller with the spec file
echo "Running PyInstaller..."
pyinstaller team_formation_api.spec --noconfirm

# Move the output to the expected location
echo "Moving bundle to python-dist/..."
mv dist/team_formation_api python-dist

# Verify the bundle
echo "Verifying bundle..."
if [ -f "python-dist/team_formation_api" ]; then
    echo "Bundle created successfully: python-dist/team_formation_api"
elif [ -f "python-dist/team_formation_api.exe" ]; then
    echo "Bundle created successfully: python-dist/team_formation_api.exe"
else
    echo "ERROR: Bundle executable not found!"
    exit 1
fi

# Quick smoke test: check that the executable starts and responds to health check
echo "Running smoke test..."
python-dist/team_formation_api &
BACKEND_PID=$!

# Wait for the backend to start
sleep 5

# Check health endpoint
if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "Smoke test PASSED: backend responds to /health"
else
    echo "WARNING: Smoke test failed (backend may need more startup time)"
fi

# Clean up
kill $BACKEND_PID 2>/dev/null || true
wait $BACKEND_PID 2>/dev/null || true

# Clean up PyInstaller artifacts
rm -rf build

echo "=== Python backend build complete ==="
echo "Output: $DESKTOP_DIR/python-dist/"
