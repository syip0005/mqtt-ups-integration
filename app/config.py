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
    "identifiers": ["ups_mqtt_integration"],
    "name": "UPS",
    "model": "Unknown",
    "manufacturer": "Unknown",
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
        "key": "battery_runtime_",
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
    {
        "name": "UPS Input Voltage",
        "key": "input_voltage_",
        "unit": "V",
        "device_class": "voltage",
        "icon": "mdi:current-ac",
        "state_class": "measurement",
        "enabled_by_default": True,
        "value_key": "input.voltage",
    },
    {
        "name": "UPS Battery Voltage",
        "key": "battery_voltage_",
        "unit": "V",
        "device_class": "voltage",
        "icon": "mdi:battery-heart-variant",
        "state_class": "measurement",
        "enabled_by_default": True,
        "value_key": "battery.voltage",
    },
    {
        "name": "UPS Nominal Power",
        "key": "ups_nominal_power",
        "unit": "W",
        "device_class": "power",
        "icon": "mdi:flash",
        "state_class": "measurement",
        "enabled_by_default": True,
        "value_key": "ups.realpower.nominal",
    },
    {
        "name": "UPS Model",
        "key": "ups_model",
        "icon": "mdi:information-outline",
        "enabled_by_default": True,
        "value_key": "ups.model",
    },
]
