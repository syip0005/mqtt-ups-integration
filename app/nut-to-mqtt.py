#!/usr/bin/env python3
import time
import json
import subprocess
import paho.mqtt.client as mqtt
import logging

# Configuration
MQTT_BROKER = "192.168.1.6"
MQTT_PORT = 1883
MQTT_USERNAME = "mqtt-user"
MQTT_PASSWORD = "mqtt"
MQTT_TOPIC_BASE = "homeassistant/sensor/ups"
DISCOVERY_PREFIX = "homeassistant"
UPS_NAME = "cyberpower@localhost"
POLL_INTERVAL = 2  # seconds

# Device info for Home Assistant
DEVICE_INFO = {
    "identifiers": ["cyberpower_cp1600epfclcd_au"],
    "name": "CyberPower UPS",
    "model": "CP1600EPFCLCD-AU",
    "manufacturer": "CyberPower Systems",
    "serial_number": "BH8PZ2000287",
}

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def restart_nut_driver():
    """Restart NUT driver when connection is lost"""
    try:
        logger.warning("Attempting to restart NUT driver...")

        # Stop driver
        subprocess.run(["sudo", "upsdrvctl", "stop"], capture_output=True, timeout=30)
        time.sleep(2)

        # Start driver
        result = subprocess.run(
            ["sudo", "upsdrvctl", "start"], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            logger.info("NUT driver restarted successfully")
            time.sleep(5)  # Give it time to initialize
            return True
        else:
            logger.error(f"Failed to restart NUT driver: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error restarting NUT driver: {e}")
        return False


def get_ups_data():
    """Get UPS data using upsc command with automatic recovery"""
    try:
        result = subprocess.run(
            ["upsc", UPS_NAME], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = {}
            for line in result.stdout.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    data[key.strip()] = value.strip()
            return data
        else:
            logger.error(f"upsc command failed: {result.stderr}")
            # Try to restart driver if upsc fails
            if (
                "Error: Driver not connected" in result.stderr
                or "Data stale" in result.stderr
            ):
                logger.warning("Detected NUT connection issue, attempting restart...")
                restart_nut_driver()
            return None
    except subprocess.TimeoutExpired:
        logger.error("upsc command timed out")
        return None
    except Exception as e:
        logger.error(f"Error getting UPS data: {e}")
        return None


def publish_discovery_config(client):
    """Publish Home Assistant MQTT Discovery configuration for 4 sensors only"""

    sensors = [
        {
            "name": "UPS Battery Charge",
            "key": "battery_charge",
            "unit": "%",
            "device_class": "battery",
            "icon": "mdi:battery",
            "state_class": "measurement",
            "enabled_by_default": True,
        },
        {
            "name": "UPS Battery Runtime",
            "key": "battery_runtime",
            "unit": "s",
            "icon": "mdi:timer-outline",
            "state_class": "measurement",
            "enabled_by_default": True,
        },
        {
            "name": "UPS Load",
            "key": "ups_load",
            "unit": "%",
            "device_class": "power_factor",
            "icon": "mdi:gauge",
            "state_class": "measurement",
            "enabled_by_default": True,
        },
        {
            "name": "UPS Status",
            "key": "ups_status",
            "icon": "mdi:power-plug",
            "enabled_by_default": True,
        },
        {
            "name": "UPS Output Voltage",
            "key": "output_voltage",
            "unit": "V",
            "device_class": "voltage",
            "icon": "mdi:current-ac",
            "state_class": "measurement",
            "enabled_by_default": True,
        },
    ]

    for sensor in sensors:
        config = {
            "name": sensor["name"],
            "unique_id": f"ups_{sensor['key']}",
            "state_topic": f"{MQTT_TOPIC_BASE}/{sensor['key']}",
            "device": DEVICE_INFO,
            "availability_topic": f"{MQTT_TOPIC_BASE}/availability",
            "icon": sensor["icon"],
            "enabled_by_default": True,
        }

        # Add optional attributes if they exist
        if sensor.get("unit"):
            config["unit_of_measurement"] = sensor["unit"]
        if sensor.get("device_class"):
            config["device_class"] = sensor["device_class"]
        if sensor.get("state_class"):
            config["state_class"] = sensor["state_class"]
        if sensor.get("enabled_by_default") is not None:
            config["enabled_by_default"] = sensor["enabled_by_default"]

        # Publish discovery config
        discovery_topic = f"{DISCOVERY_PREFIX}/sensor/ups_{sensor['key']}/config"
        client.publish(discovery_topic, json.dumps(config), retain=True)
        logger.info(f"Published discovery config for {sensor['name']}")

    # Publish availability as online
    client.publish(f"{MQTT_TOPIC_BASE}/availability", "online", retain=True)


def publish_to_mqtt(client, data):
    """Publish only the 4 key UPS metrics to MQTT"""
    if not data:
        return

    # Only extract the 5 metrics we want (using exact field names from your UPS)
    metrics = {
        "battery_charge": data.get("battery.charge"),
        "battery_runtime": data.get("battery.runtime"),
        "ups_load": data.get("ups.load"),
        "ups_status": data.get("ups.status"),
        "output_voltage": data.get("output.voltage"),
    }

    # Convert status codes to human readable
    status_map = {
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

    # Parse and convert UPS status
    if metrics["ups_status"]:
        status_codes = metrics["ups_status"].split()
        readable_status = []
        for code in status_codes:
            readable_status.append(status_map.get(code, code))
        metrics["ups_status"] = " + ".join(readable_status)

    # Publish individual metrics (only if they exist)
    published_count = 0
    for metric, value in metrics.items():
        if value is not None:
            topic = f"{MQTT_TOPIC_BASE}/{metric}"
            try:
                client.publish(topic, str(value), retain=True)
                published_count += 1
                logger.debug(f"Published {metric}: {value}")
            except Exception as e:
                logger.error(f"Error publishing {metric}: {e}")

    # Log summary
    if published_count > 0:
        # Calculate runtime in minutes for display
        runtime_display = "N/A"
        if metrics["battery_runtime"]:
            try:
                runtime_min = int(float(metrics["battery_runtime"])) // 60
                runtime_sec = int(float(metrics["battery_runtime"])) % 60
                runtime_display = f"{runtime_min}m{runtime_sec}s"
            except Exception:
                runtime_display = f"{metrics['battery_runtime']}s"

        logger.info(
            f"Published {published_count}/5 metrics - "
            f"Battery: {metrics['battery_charge']}%, "
            f"Runtime: {runtime_display}, "
            f"Load: {metrics['ups_load']}%, "
            f"Status: {metrics['ups_status']}, "
            f"Output: {metrics['output_voltage']}V"
        )
    else:
        logger.warning("No metrics were published")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        # Publish discovery configuration when connected
        publish_discovery_config(client)
    else:
        logger.error(f"Failed to connect to MQTT broker: {rc}")


def on_disconnect(client, userdata, rc):
    logger.warning("Disconnected from MQTT broker")


def main():
    # Setup MQTT client
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    # Set last will and testament
    client.will_set(f"{MQTT_TOPIC_BASE}/availability", "offline", retain=True)

    try:
        logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        logger.info("Starting UPS monitoring with 5 metrics...")
        logger.info(
            "Monitoring: battery.charge, battery.runtime, ups.load, ups.status, output.voltage"
        )

        # Give connection time to establish
        time.sleep(2)

        while True:
            ups_data = get_ups_data()
            if ups_data:
                publish_to_mqtt(client, ups_data)
            else:
                logger.warning("No UPS data received")
                client.publish(
                    f"{MQTT_TOPIC_BASE}/availability", "offline", retain=True
                )

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Mark as offline before disconnecting
        client.publish(f"{MQTT_TOPIC_BASE}/availability", "offline", retain=True)
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
