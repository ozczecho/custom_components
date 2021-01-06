"""Support for the Airthouch 3 Unit."""
import logging

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    CURRENT_HVAC_OFF,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_DRY,
    CURRENT_HVAC_IDLE,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, TEMP_CELSIUS
import homeassistant.helpers.config_validation as cv

from custom_components.airtouch3.vzduch import (
    AC_POWER_ON,
    AC_POWER_OFF,
    AC_FAN_MODE_QUIET,
    AC_FAN_MODE_LOW,
    AC_FAN_MODE_MEDIUM,
    AC_FAN_MODE_HIGH,
    AC_FAN_MODE_POWERFUL,
    AC_FAN_MODE_AUTO,
    AC_MODE_HEAT,
    AC_MODE_COOL,
    AC_MODE_FAN,
    AC_MODE_DRY,
    AC_MODE_AUTO
)

from . import DOMAIN as AT3_DOMAIN
from .const import (
    ATTR_INSIDE_TEMPERATURE,
    FAN_QUIET,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    FAN_POWERFUL,
    FAN_AUTO 
)

_LOGGER = logging.getLogger(__name__)

HA_STATE_TO_AT3 = {
    HVAC_MODE_OFF :-1,
    HVAC_MODE_HEAT: AC_MODE_HEAT,
    HVAC_MODE_COOL: AC_MODE_COOL,
    HVAC_MODE_FAN_ONLY: AC_MODE_FAN,
    HVAC_MODE_DRY: AC_MODE_DRY,
    HVAC_MODE_HEAT_COOL: AC_MODE_AUTO,
}

AT3_TO_HA_STATE = {
   -1: HVAC_MODE_OFF,
    AC_MODE_HEAT: HVAC_MODE_HEAT,
    AC_MODE_COOL: HVAC_MODE_COOL,
    AC_MODE_FAN: HVAC_MODE_FAN_ONLY,
    AC_MODE_DRY: HVAC_MODE_DRY,
    AC_MODE_AUTO: HVAC_MODE_HEAT_COOL
}

HA_STATE_TO_CURRENT_STATE = {
    HVAC_MODE_OFF : CURRENT_HVAC_OFF,
    HVAC_MODE_HEAT: CURRENT_HVAC_HEAT,
    HVAC_MODE_COOL: CURRENT_HVAC_COOL,
    HVAC_MODE_FAN_ONLY: CURRENT_HVAC_IDLE,
    HVAC_MODE_DRY: CURRENT_HVAC_DRY,
    HVAC_MODE_HEAT_COOL: CURRENT_HVAC_IDLE
}

HA_FAN_MODE_TO_AT3 = {
    FAN_QUIET : AC_FAN_MODE_QUIET,
    FAN_LOW : AC_FAN_MODE_LOW,
    FAN_MEDIUM : AC_FAN_MODE_MEDIUM,
    FAN_HIGH : AC_FAN_MODE_HIGH,
    FAN_POWERFUL : AC_FAN_MODE_POWERFUL,
    FAN_AUTO : AC_FAN_MODE_AUTO
}

AT3_TO_HA_FAN_MODE = {
    AC_FAN_MODE_QUIET: FAN_QUIET,
    AC_FAN_MODE_LOW: FAN_LOW,
    AC_FAN_MODE_MEDIUM: FAN_MEDIUM,
    AC_FAN_MODE_HIGH: FAN_HIGH,
    AC_FAN_MODE_POWERFUL: FAN_POWERFUL,
    AC_FAN_MODE_AUTO: FAN_AUTO
}

TEMPERATURE_PRECISION = 1
TARGET_TEMPERATURE_STEP = 1

SUPPORTED_FEATURES = \
    SUPPORT_TARGET_TEMPERATURE | \
    SUPPORT_FAN_MODE 

CLIMATE_ICON = "mdi:home-variant-outline"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up AirTouch3 climate based on config_entry."""
    vzduch_api = hass.data[AT3_DOMAIN].get(entry.entry_id)
    _LOGGER.debug(f"[AT3Climate] Init {vzduch_api.name}")
    async_add_entities([AirTouch3Climate(vzduch_api)], update_before_add=True)


class AirTouch3Climate(ClimateEntity):
    """Representation of a AirTouch3 Unit."""

    def __init__(self, api):
        """Initialize"""
        self._api = api
        self._list = {
            ATTR_HVAC_MODE: list(HA_STATE_TO_AT3),
            ATTR_FAN_MODE: list(HA_FAN_MODE_TO_AT3)
        }
        self._supported_features = SUPPORTED_FEATURES

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return self._api.device_info

    @property
    def icon(self):
        """Front End Icon"""
        return CLIMATE_ICON

    @property
    def name(self):
        """Return the name of the thermostat, if any."""
        return self._api.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._api.airtouch_id

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        return TEMP_CELSIUS

    @property
    def precision(self):
        """Return the precision of the temperature in the system."""
        return TEMPERATURE_PRECISION

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._api.room_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._api.desired_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return TARGET_TEMPERATURE_STEP

    @property
    def hvac_action(self):
        """The current HVAC action (heating, cooling)"""
        if self._api.power == AC_POWER_OFF:
            return CURRENT_HVAC_OFF
            
        ac_mode = self._api.mode
        return HA_STATE_TO_CURRENT_STATE.get(AT3_TO_HA_STATE.get(ac_mode, HVAC_MODE_HEAT_COOL), CURRENT_HVAC_IDLE)

    @property
    def hvac_mode(self):
        """Return current operation ie. heat, cool, idle."""
        ac_mode = self._api.mode
        return AT3_TO_HA_STATE.get(ac_mode, HVAC_MODE_HEAT_COOL)

    @property
    def hvac_modes(self):
        """Return the list of available operation modes."""
        return self._list.get(ATTR_HVAC_MODE)

    @property
    def fan_mode(self):
        """Return the fan setting."""
        ac_fan_mode = self._api.fan_mode
        return AT3_TO_HA_FAN_MODE.get(ac_fan_mode, FAN_LOW)

    @property
    def fan_modes(self):
        """List of available fan modes."""
        return self._list.get(ATTR_FAN_MODE)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        if hvac_mode == HVAC_MODE_OFF:
            _LOGGER.debug("[AT3Climate] async_set_hvac_mode Turning AC OFF")
            await self._api.power_switch(AC_POWER_OFF)
        else:
            _LOGGER.debug(f"[AT3Climate] async_set_hvac_mode Setting hvac_mode mode to {hvac_mode}")
            if self._api.power == AC_POWER_OFF:
                await self._api.power_switch(AC_POWER_ON)
            
            await self._api.set_mode(HA_STATE_TO_AT3.get(hvac_mode)) #MBTODO

    async def async_set_fan_mode(self, fan_mode):
        """Set fan mode."""
        await self._api.set_fan_mode(HA_FAN_MODE_TO_AT3.get(fan_mode)) 

    async def async_set_temperature(self, **kwargs):
        """Set the desired temperature"""
        _LOGGER.debug(f"[AT3Climate] async_set_temperature [{kwargs}]")
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            _LOGGER.debug(f"[AT3Climate] async_set_temperature Set temperature to [{temperature}]")
            await self._api.set_temperature(temperature)

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()