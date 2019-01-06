"""
Support for NuHeat thermostats.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/nuheat/

This is a wrapper for the component included with Home Assistant.
"""
import logging

import voluptuous as vol

from homeassistant.const import CONF_REGION, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery

REQUIREMENTS = ["nuheat==0.3.0"]

_LOGGER = logging.getLogger(__name__)

DOMAIN = "nuheat"

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_REGION): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_DEVICES, default=[]):
            vol.All(cv.ensure_list, [cv.string]),
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the NuHeat thermostat component."""
    import nuheat

    conf = config[DOMAIN]
    region = conf.get(CONF_REGION)
    username = conf.get(CONF_USERNAME)
    password = conf.get(CONF_PASSWORD)
    devices = conf.get(CONF_DEVICES)

    api = nuheat.NuHeat(region, username, password)
    api.authenticate()
    hass.data[DOMAIN] = (api, devices)

    discovery.load_platform(hass, "climate", DOMAIN, {}, config)
    return True
