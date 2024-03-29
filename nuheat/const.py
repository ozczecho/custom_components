"""Constants for NuHeat thermostats."""
from homeassistant.const import Platform

DOMAIN = "nuheat"

PLATFORMS = [Platform.CLIMATE]

CONF_SERIAL_NUMBER = "serial_number"

CONF_BRAND = "brand"

MANUFACTURER = "NuHeat"

NUHEAT_API_STATE_SHIFT_DELAY = 2