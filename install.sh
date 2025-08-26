#!/bin/bash
set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Make sure run.sh is executable
chmod +x run.sh

# Install the systemd service
echo "Installing systemd service..."
# Stop the old service if it exists
if sudo systemctl is-active --quiet mqtt-ups-integration.service; then
    echo "Stopping old service..."
    sudo systemctl stop mqtt-ups-integration.service
    sudo systemctl disable mqtt-ups-integration.service
fi

# Install the systemd service for the current user
SERVICE_NAME="mqtt-ups-integration@$USER.service"
echo "Installing systemd service as $SERVICE_NAME..."
sudo cp mqtt-ups-integration.service "/etc/systemd/system/mqtt-ups-integration@.service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "Service installed and enabled."
echo "You can start it with: sudo systemctl start $SERVICE_NAME"
echo "You can check its status with: sudo systemctl status $SERVICE_NAME"