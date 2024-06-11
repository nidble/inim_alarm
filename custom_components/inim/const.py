"""Component level custom constants."""

from datetime import timedelta
from typing import Final

DOMAIN = "inim"

CONF_CLIENT_ID: Final = "client_id"
CONF_DEVICE_ID: Final = "device_id"
CONF_SCENARIOS: Final = "scenarios"

CONNECTION: Final = "connection"

# from homeassistant.components.binary_sensor import (SCAN_INTERVAL as DEFAULT_SCAN_INTERVAL)
DEFAULT_SCAN_INTERVAL = timedelta(seconds=5)
