#!/bin/bash
set -e

# Change to the script's directory
cd "$(dirname "$0")"

# Make sure run.sh is executable
chmod +x run.sh

# Check if the script is run as root
if [ "$EUID" -eq 0 ]; then
  echo "Please do not run this script as root"
  exit 1
fi

# Ask for the sudo password upfront
sudo -v

# Keep-alive: update existing sudo time stamp if set, otherwise do nothing.
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Configure NUT service
echo "Configuring NUT..."
sudo sed -i 's/^MODE=.*/MODE=standalone/' /etc/nut/nut.conf
echo "MONITOR cyberpower@localhost 1 zoga 123456 master" | sudo tee -a /etc/nut/upsmon.conf > /dev/null

# Start NUT services
echo "Ensuring NUT services are running..."
sudo systemctl enable nut-server.service
sudo systemctl start nut-server.service
sudo systemctl enable nut-client.service
sudo systemctl start nut-client.service

# Install our application's systemd service
echo "Installing systemd service..."
if sudo systemctl is-active --quiet "mqtt-ups-integration@$USER.service"; then
    echo "Restarting existing service..."
    sudo systemctl restart "mqtt-ups-integration@$USER.service"
fi

# Install the systemd service for the current user
SERVICE_NAME="mqtt-ups-integration@$USER.service"
echo "Installing systemd service as $SERVICE_NAME..."
sudo cp mqtt-ups-integration.service "/etc/systemd/system/mqtt-ups-integration@.service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

# Start or restart the service
if ! sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl start "$SERVICE_NAME"
    echo "Service started."
else
    echo "Service is already running. It has been restarted to apply changes."
fi

echo ""
echo "Service installed and enabled."
echo "The service is now running in the background."
echo "You can check its status with: sudo systemctl status $SERVICE_NAME"