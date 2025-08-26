"""
MQTT Client module for publishing UPS data to MQTT broker.
Handles connection, discovery configuration, and data publishing.
"""

import json
import logging
from typing import Dict, Optional
import paho.mqtt.client as mqtt

from app.config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    MQTT_TOPIC_BASE,
    DISCOVERY_PREFIX,
    DEVICE_INFO,
    SENSORS,
    STATUS_MAP,
)

# Setup logging
logger = logging.getLogger(__name__)


class MQTTClient:
    """Client for publishing UPS data to MQTT broker"""

    def __init__(self):
        """Initialize the MQTT client"""
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Set last will and testament
        self.client.will_set(f"{MQTT_TOPIC_BASE}/availability", "offline", retain=True)
        self.discovery_published = False

    def connect(self) -> None:
        """Connect to the MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker"""
        try:
            # Mark as offline before disconnecting
            self.client.publish(
                f"{MQTT_TOPIC_BASE}/availability", "offline", retain=True
            )
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            # Publish availability as online
            self.client.publish(f"{MQTT_TOPIC_BASE}/availability", "online", retain=True)
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        logger.warning("Disconnected from MQTT broker")

    def publish_discovery_config(self, device_info: Dict[str, str]) -> None:
        """Publish Home Assistant MQTT Discovery configuration for sensors"""
        base_device_info = {
            "identifiers": device_info.get("serial_number", "ups_mqtt_integration"),
            "name": device_info.get("model", "UPS"),
            "model": device_info.get("model", "Unknown"),
            "manufacturer": device_info.get("manufacturer", "Unknown"),
            "serial_number": device_info.get("serial_number"),
        }

        for sensor in SENSORS:
            config = {
                "name": f"{base_device_info['name']} {sensor['name']}",
                "unique_id": f"ups_{sensor['key']}",
                "state_topic": f"{MQTT_TOPIC_BASE}/{sensor['key']}",
                "device": base_device_info,
                "availability_topic": f"{MQTT_TOPIC_BASE}/availability",
                "icon": sensor["icon"],
            }

            if sensor.get("unit"):
                config["unit_of_measurement"] = sensor["unit"]
            if sensor.get("device_class"):
                config["device_class"] = sensor["device_class"]
            if sensor.get("state_class"):
                config["state_class"] = sensor["state_class"]
            if sensor.get("enabled_by_default") is not None:
                config["enabled_by_default"] = sensor["enabled_by_default"]

            discovery_topic = (
                f"{DISCOVERY_PREFIX}/sensor/ups_{sensor['key']}/config"
            )
            self.client.publish(discovery_topic, json.dumps(config), retain=True)
            logger.info(f"Published discovery config for {sensor['name']}")

        self.discovery_published = True

    def publish_data(self, data: Optional[Dict[str, str]]) -> None:
        """
        Publish UPS data to MQTT.

        Args:
            data: Dictionary of UPS data from the UPS client
        """
        if not data:
            logger.warning("No UPS data to publish")
            self.client.publish(
                f"{MQTT_TOPIC_BASE}/availability", "offline", retain=True
            )
            return

        # Update and publish discovery config if not already done
        if not self.discovery_published:
            device_info = {
                "model": data.get("device.model"),
                "manufacturer": data.get("device.mfr"),
                "serial_number": data.get("device.serial"),
            }
            self.publish_discovery_config(device_info)

        # Extract metrics based on sensor definitions
        metrics = {}
        for sensor in SENSORS:
            metrics[sensor["key"]] = data.get(sensor["value_key"])

        # Parse and convert UPS status
        if metrics["ups_status"]:
            status_codes = metrics["ups_status"].split()
            readable_status = []
            for code in status_codes:
                readable_status.append(STATUS_MAP.get(code, code))
            metrics["ups_status"] = " + ".join(readable_status)

        # Publish individual metrics (only if they exist)
        published_count = 0
        for metric, value in metrics.items():
            if value is not None:
                topic = f"{MQTT_TOPIC_BASE}/{metric}"
                try:
                    self.client.publish(topic, str(value), retain=True)
                    published_count += 1
                    logger.debug(f"Published {metric}: {value}")
                except Exception as e:
                    logger.error(f"Error publishing {metric}: {e}")

        # Log summary
        if published_count > 0:
            # Calculate runtime in minutes for display
            runtime_display = "N/A"
            if metrics["battery_runtime_"]:
                try:
                    runtime_min = int(float(metrics["battery_runtime_"])) // 60
                    runtime_sec = int(float(metrics["battery_runtime_"])) % 60
                    runtime_display = f"{runtime_min}m{runtime_sec}s"
                except Exception:
                    runtime_display = f"{metrics['battery_runtime_']}s"

            logger.info(
                f"Published {published_count}/{len(SENSORS)} metrics - "
                f"Battery: {metrics['battery_charge']}%, "
                f"Runtime: {runtime_display}, "
                f"Load: {metrics['ups_load']}%, "
                f"Status: {metrics['ups_status']}, "
                f"Input: {metrics['input_voltage_']}V, "
                f"Output: {metrics['output_voltage']}V, "
                f"Battery Voltage: {metrics['battery_voltage_']}V"
            )
        else:
            logger.warning("No metrics were published")
