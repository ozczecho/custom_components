"""Support for AirTouch3 zones."""
import logging

from homeassistant.helpers.entity import ToggleEntity

from . import DOMAIN as AT3_DOMAIN

_LOGGER = logging.getLogger(__name__)

ZONE_ICON = "mdi:map-marker"

ZONE_ON = 1
ZONE_OFF = 0

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AirTouch3 zones."""
    vzduch_api = hass.data[AT3_DOMAIN].get(entry.entry_id)
    _LOGGER.debug(f"[AT3Zone] Init {vzduch_api.name}")
    zones = vzduch_api.zones
    if zones:
        async_add_entities(
            [
                ZoneSwitch(vzduch_api, zone.id)
                for zone_index, zone in enumerate(zones)
            ]
        )

class ZoneSwitch(ToggleEntity):
    """AirTouch3 zone."""

    def __init__(self, api, zone_id):
        """Initialize the zone."""
        _LOGGER.debug(f"[AT3Zone] Zone ID Is {zone_id}")
        zone_id_filter = filter(lambda x: x.id == zone_id, api.zones)

        self._api = api
        self._zone = next(zone_id_filter)

    @property
    def icon(self):
        """Front End Icon"""
        return ZONE_ICON

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
    def fan_value(self):
        """Returns the fan % value"""
        return self._zone.fan_value

    @property
    def is_spill(self):
        """Returns whether zone is used as a spill."""
        return self._zone.is_spill

    @property
    def device_state_attributes(self):
        """attributes for the zone"""
        return {
            "zone_temperature_type": self._zone.zone_temperature_type, 
            "fan_value": self._zone.fan_value,
            "is_spill": self._zone.is_spill
            }

    @property
    def zone_temperature_type(self):
        """Return the zone temperature type."""
        return self._zone.zone_temperature_type

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        _LOGGER.debug(f"[AT3Zone] async_turn_on")
        await self._api.zone_switch(self._zone.id, ZONE_ON)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        _LOGGER.debug(f"[AT3Zone] async_turn_off")
        await self._api.zone_switch(self._zone.id, ZONE_OFF)

    async def async_toggle(self, **kwargs):
        """Toggle the entity."""
        _LOGGER.debug(f"[AT3Zone] async_toggle")
        await self._api.zone_toggle(self._zone.id)