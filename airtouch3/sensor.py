"""Support for AirTouch 3 sensors."""

import logging

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
    TEMP_CELSIUS
)
from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_INSIDE_TEMPERATURE,
    SENSOR_TYPE_TEMPERATURE,
)

from . import DOMAIN as AT3_DOMAIN

SENSOR_ICON = "mdi:home-thermometer-outline"

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AirTouch 3 sensor based on config_entry."""
    vzduch_api = hass.data[AT3_DOMAIN].get(entry.entry_id)
    _LOGGER.debug(f"[AT3Sensor] Init {vzduch_api.name}")
    sensors = vzduch_api.sensors
    if sensors:
        async_add_entities(
            [
                AT3Sensor(vzduch_api, sensor.id)
                for sensor_index, sensor in enumerate(sensors)
                if sensor.is_available
            ]
        )

class AT3Sensor(Entity):
    """Representation of a AirTouch 3 temperature sensor."""

    def __init__(self, api, sensor_id):
        """Initialize the sensor."""
        _LOGGER.debug(f"[AT3Sensor] Sensor ID Is {sensor_id}")
        sensor_id_filter = filter(lambda x: x.id == sensor_id, api.sensors)

        self._api = api
        self._sensor = next(sensor_id_filter)

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._api.airtouch_id}-{self._sensor.id}"

    @property
    def icon(self):
        """Front End Icon"""
        return SENSOR_ICON

    @property
    def id(self):
        """Returns sensor id"""
        return self._sensor.id

    @property
    def is_available(self):
        """Returns sensor availability"""
        return self._sensor.is_available

    @property
    def is_low_battery(self):
        """Returns sensor battery level"""
        return self._sensor.is_low_battery

    @property
    def state(self):
        """Returns sensor temperature"""
        return self._sensor.temperature

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return SENSOR_TYPE_TEMPERATURE

    @property
    def device_state_attributes(self):
        """attributes for the sensor"""
        return {
            "is_available": self._sensor.is_available, 
            "is_low_battery": self._sensor.is_low_battery
            }        

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()