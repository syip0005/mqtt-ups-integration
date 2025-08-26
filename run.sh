#!/bin/bash
set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Define path to uv
UV_PATH="$HOME/.local/bin/uv"

# Check if uv is installed
if [ ! -f "$UV_PATH" ]; then
    echo "uv is not installed at $UV_PATH. Please install it first."
    echo "You can install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Set up the virtual environment
echo "Syncing environment with uv..."
"$UV_PATH" venv
"$UV_PATH" sync

# Activate the virtual environment and run the application
echo "Starting application..."
"$UV_PATH" run python run.py