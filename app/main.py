#!/usr/bin/env python3
"""
Main entry point for the UPS to MQTT integration.
Monitors UPS data and publishes it to MQTT for Home Assistant.
"""

import time
import logging
from typing import NoReturn

from app.config import POLL_INTERVAL
from app.ups_client import UPSClient
from app.mqtt_client import MQTTClient

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> NoReturn:
    """
    Main function to run the UPS to MQTT integration.
    Initializes clients, connects to MQTT broker, and starts monitoring loop.
    """
    # Initialize clients
    ups_client = UPSClient()
    mqtt_client = MQTTClient()

    try:
        # Connect to MQTT broker
        mqtt_client.connect()

        logger.info("Starting UPS monitoring...")
        logger.info(
            "Monitoring metrics: battery.charge, battery.runtime, ups.load, ups.status, output.voltage, input.voltage, battery.voltage, ups.realpower.nominal, ups.model"
        )

        # Give connection time to establish
        time.sleep(2)

        # Main monitoring loop
        while True:
            # Get UPS data
            ups_data = ups_client.get_data()

            # Publish data to MQTT
            mqtt_client.publish_data(ups_data)

            # Wait for next poll
            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Disconnect from MQTT broker
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
