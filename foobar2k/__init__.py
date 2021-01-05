"""Foobar2k Media Player."""
import asyncio
import logging

from custom_components.foobar2k.foobar2k import Foobar2k
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TIMEOUT
from .const import DOMAIN, TIMEOUT
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util import Throttle

from . import config_flow  # noqa: F401

_LOGGER = logging.getLogger(__name__)
PLATFORM = "media_player"

async def async_setup(hass, config):
    """Connect to Foobar2k Server"""
    if DOMAIN not in config:
        return True

    host = config[DOMAIN][CONF_HOST]
    if not host:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}
            )
        )
 
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: host}
        )
    )
    return True

async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    """Connect to Foobar2k Server"""
    conf = entry.data

    foobar2k_api = await api_init( hass, conf[CONF_HOST], conf.get(CONF_PORT), )
    if not foobar2k_api:
        return False

    hass.data.setdefault(DOMAIN, {}).update({entry.entry_id: foobar2k_api})
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, PLATFORM))

    return True

async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await asyncio.wait( [ hass.config_entries.async_forward_entry_unload(config_entry, PLATFORM)] )
    hass.data[DOMAIN].pop(config_entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return True

async def api_init(hass, host, port, timeout = TIMEOUT):
    """Init the Foobar2k Server."""

    session = hass.helpers.aiohttp_client.async_get_clientsession()
    try:
        _LOGGER.debug(f"We have host {host} port {port}")
        device = Foobar2k(session, host, port, timeout)

        await device.async_update()
    except asyncio.TimeoutError:
        _LOGGER.debug("Connection to %s timed out", host)
        raise ConfigEntryNotReady
    except ClientConnectionError:
        _LOGGER.debug("ClientConnectionError to %s", host)
        raise ConfigEntryNotReady
    except Exception:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error creating device %s", host)
        return None

    return device

async def update_listener(hass, config_entry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)