"""
UPS Client module for interacting with Network UPS Tools (NUT).
Handles data retrieval and driver management.
"""

import time
import subprocess
import logging
from typing import Dict, Optional

from app.config import UPS_NAME

# Setup logging
logger = logging.getLogger(__name__)


class UPSClient:
    """Client for interacting with Network UPS Tools (NUT)"""

    def __init__(self, ups_name: str = UPS_NAME):
        """
        Initialize the UPS client.

        Args:
            ups_name: The name of the UPS in NUT format (e.g., 'cyberpower@localhost')
        """
        self.ups_name = ups_name

    def get_data(self) -> Optional[Dict[str, str]]:
        """
        Get UPS data using upsc command with automatic recovery.

        Returns:
            Dictionary of UPS data or None if retrieval failed
        """
        try:
            result = subprocess.run(
                ["upsc", self.ups_name], capture_output=True, text=True, timeout=10
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
                    logger.warning(
                        "Detected NUT connection issue, attempting restart..."
                    )
                    self.restart_driver()
                return None
        except subprocess.TimeoutExpired:
            logger.error("upsc command timed out")
            return None
        except Exception as e:
            logger.error(f"Error getting UPS data: {e}")
            return None

    def restart_driver(self) -> bool:
        """
        Restart NUT driver when connection is lost.

        Returns:
            True if restart was successful, False otherwise
        """
        try:
            logger.warning("Attempting to restart NUT driver...")

            # Stop driver
            subprocess.run(
                ["sudo", "upsdrvctl", "stop"], capture_output=True, timeout=30
            )
            time.sleep(2)

            # Start driver
            result = subprocess.run(
                ["sudo", "upsdrvctl", "start"],
                capture_output=True,
                text=True,
                timeout=30,
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
