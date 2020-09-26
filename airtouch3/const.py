"""Constants for AirTouch 3."""
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    TEMP_CELSIUS,
    PERCENTAGE,
)

DEFAULT_PORT = 8899
DOMAIN = "airtouch3"
TIMEOUT = 60

ATTR_INSIDE_TEMPERATURE = "inside_temperature"

FAN_QUIET = "Quiet"
FAN_LOW = "Low"
FAN_MEDIUM = "Medium"
FAN_HIGH = "High"
FAN_POWERFUL = "Powerful"
FAN_AUTO = "Auto"

SENSOR_TYPE_TEMPERATURE = "temperature"