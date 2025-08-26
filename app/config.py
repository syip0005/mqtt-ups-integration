"""
Configuration module for the UPS to MQTT integration.
Loads configuration from .env file and provides sensor definitions.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPIC_BASE = os.getenv("MQTT_TOPIC_BASE", "homeassistant/sensor/ups")
DISCOVERY_PREFIX = os.getenv("DISCOVERY_PREFIX", "homeassistant")

# UPS Configuration
UPS_NAME = os.getenv("UPS_NAME", "cyberpower@localhost")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))

# Device Information
DEVICE_INFO = {
    "identifiers": [os.getenv("DEVICE_IDENTIFIER", "cyberpower_cp1600epfclcd_au")],
    "name": os.getenv("DEVICE_NAME", "CyberPower UPS"),
    "model": os.getenv("DEVICE_MODEL", "CP1600EPFCLCD-AU"),
    "manufacturer": os.getenv("DEVICE_MANUFACTURER", "CyberPower Systems"),
    "serial_number": os.getenv("DEVICE_SERIAL_NUMBER", "BH8PZ2000287"),
}

# Status code mapping
STATUS_MAP = {
    "OL": "Online",
    "OB": "On Battery",
    "LB": "Low Battery",
    "HB": "High Battery",
    "RB": "Replace Battery",
    "CHRG": "Charging",
    "DISCHRG": "Discharging",
    "BYPASS": "Bypass",
    "CAL": "Calibrating",
    "OFF": "Offline",
    "OVER": "Overload",
    "TRIM": "Smart Trim",
    "BOOST": "Smart Boost",
}

# Sensor definitions
SENSORS = [
    {
        "name": "UPS Battery Charge",
        "key": "battery_charge",
        "unit": "%",
        "device_class": "battery",
        "icon": "mdi:battery",
        "state_class": "measurement",
        "enabled_by_default": True,
        "value_key": "battery.charge",
    },
    {
        "name": "UPS Battery Runtime",
        "key": "battery_runtime",
        "unit": "s",
        "icon": "mdi:timer-outline",
        "state_class": "measurement",
        "enabled_by_default": True,
        "value_key": "battery.runtime",
    },
    {
        "name": "UPS Load",
        "key": "ups_load",
        "unit": "%",
        "device_class": "power_factor",
        "icon": "mdi:gauge",
        "state_class": "measurement",
        "enabled_by_default": True,
        "value_key": "ups.load",
    },
    {
        "name": "UPS Status",
        "key": "ups_status",
        "icon": "mdi:power-plug",
        "enabled_by_default": True,
        "value_key": "ups.status",
    },
    {
        "name": "UPS Output Voltage",
        "key": "output_voltage",
        "unit": "V",
        "device_class": "voltage",
        "icon": "mdi:current-ac",
        "state_class": "measurement",
        "enabled_by_default": True,
        "value_key": "output.voltage",
    },
]
