"""
UPS to MQTT Integration Package.

This package provides functionality to monitor a UPS via Network UPS Tools (NUT)
and publish the data to MQTT for Home Assistant integration.
"""

__version__ = "1.0.0"

# Import main components for easier access
from app.config import MQTT_BROKER, MQTT_PORT, UPS_NAME, POLL_INTERVAL, DEVICE_INFO
from app.ups_client import UPSClient
from app.mqtt_client import MQTTClient

# Expose main function
from app.main import main

__all__ = [
    "UPSClient",
    "MQTTClient",
    "main",
    "MQTT_BROKER",
    "MQTT_PORT",
    "UPS_NAME",
    "POLL_INTERVAL",
    "DEVICE_INFO",
]
