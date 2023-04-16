"""Support for AirTouch3 zone Dampers."""
import logging

from homeassistant.components.fan import (FanEntity, SUPPORT_SET_SPEED)
 

from homeassistant.helpers.entity import ToggleEntity
from homeassistant.util.percentage import int_states_in_range, ranged_value_to_percentage, percentage_to_ranged_value


SPEED_RANGE = (1, 100)

SUPPORTED_FEATURES = \
    SUPPORT_SET_SPEED

from . import DOMAIN as AT3_DOMAIN

_LOGGER = logging.getLogger(__name__)

FAN_ICON = "mdi:fan"

ZONE_ON = 1
ZONE_OFF = 0

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AirTouch3 Dampers."""
    vzduch_api = hass.data[AT3_DOMAIN].get(entry.entry_id)
    _LOGGER.debug(f"[AT3Fan] Init {vzduch_api.name}")
    zones = vzduch_api.zones
    if zones:
        async_add_entities(
            [
                ZoneFan(vzduch_api, zone.id)
                for zone_index, zone in enumerate(zones)
            ]
        )

class ZoneFan(FanEntity):
    """AirTouch3 Damper."""

    def __init__(self, api, zone_id):
        """Initialize the zone."""
        _LOGGER.debug(f"[AT3Fan] Zone ID Is {zone_id}")
        zone_id_filter = filter(lambda x: x.id == zone_id, api.zones)

        self._api = api
        self._zone = next(zone_id_filter)
        self._supported_features = SUPPORTED_FEATURES

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def icon(self):
        """Front End Icon"""
        return FAN_ICON

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._api.airtouch_id}-{self._zone.id}"

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return {
            "zone name": self._zone.name,
            "id": self._zone.id
        }

    @property
    def name(self):
        """Returns zone name"""
        return self._zone.name

    @property
    def id(self):
        """Returns zone id"""
        return self._zone.id

    @property
    def status(self):
        """Returns the zone status (on / off)"""
        return self._zone.status

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._zone.status == ZONE_ON

    @property
    def percentage(self):
        """Returns the fan % value"""
        return self._zone.fan_value

    @property
    def extra_state_attributes(self):
        """attributes for the zone"""
        return {
            "fan_value": self._zone.fan_value,
            "id": self._zone.id,
            "desired_temperature": self._zone.desired_temperature
            }

    @property
    def zone_desired_temperature(self):
        """Return the zone desired temperature."""
        return self._zone.desired_temperature

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        _LOGGER.debug(f"[AT3Fan] async_turn_on")
        await self._api.zone_switch(self._zone.id, ZONE_ON)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        _LOGGER.debug(f"[AT3Fan] async_turn_off")
        await self._api.zone_switch(self._zone.id, ZONE_OFF)

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        _LOGGER.debug(f"[AT3Fan] async_toggle")
        await self._api.zone_toggle(self._zone.id)

    async def async_set_percentage(self, percentage):
        """Toggle the entity."""
        _LOGGER.debug(f"[AT3Fan] async_set_percentage")
        await self._api.set_zone_damper(self._zone.id, percentage)