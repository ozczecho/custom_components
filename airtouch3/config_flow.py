import asyncio
import logging
import voluptuous as vol

from aiohttp import ClientError, web_exceptions
from async_timeout import timeout
from custom_components.airtouch3.vzduch import Vzduch

from homeassistant import config_entries, core
from homeassistant.const import CONF_HOST, CONF_PORT

from . import config_flow
from .const import DEFAULT_PORT, DOMAIN, TIMEOUT

_LOGGER = logging.getLogger(__name__)

@config_entries.HANDLERS.register(DOMAIN)
class AirTouch3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """AirTouch 3 config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @core.callback
    def _async_get_entry(self, data):

        return self.async_create_entry(
            title=data[CONF_HOST],
            data={
                CONF_HOST: data[CONF_HOST],
                CONF_PORT: data.get(CONF_PORT)
            },
        )

    async def async_step_user(self, user_input=None):
        _LOGGER.debug("async_step_user")
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self.schema)

        errors = {}
        host = user_input[CONF_HOST]
        port = user_input[CONF_PORT]

        try:
            _LOGGER.debug("create_device")
            session = self.hass.helpers.aiohttp_client.async_get_clientsession()
            with timeout(TIMEOUT):
                _LOGGER.debug("Call vzduch")
                device = Vzduch(session, host, port, timeout)
                await device.async_update()
        except asyncio.TimeoutError:
            return self.async_show_form(
                step_id="user",
                data_schema=self.schema,
                errors={"base": "device_timeout"},
            )
        except web_exceptions.HTTPForbidden:
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "forbidden"},
            )
        except ClientError:
            _LOGGER.exception("ClientError")
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "device_fail"},
            )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating device")
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "device_fail"},
            )

        name = f"AirTouch_{device.name}"
        _LOGGER.debug(f"Device with name {name} has been setup")


        return self._async_get_entry(user_input)


    async def create_device(self, host, port=DEFAULT_PORT):
        try:
            _LOGGER.debug("create_device")
            session = self.hass.helpers.aiohttp_client.async_get_clientsession()
            with timeout(TIMEOUT):
                _LOGGER.debug("Call vzduch")
                device = await Vzduch(session, host, port, timeout)
        except asyncio.TimeoutError:
            return self.async_show_form(
                step_id="user",
                data_schema=self.schema,
                errors={"base": "device_timeout"},
            )
        except web_exceptions.HTTPForbidden:
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "forbidden"},
            )
        except ClientError:
            _LOGGER.exception("ClientError")
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "device_fail"},
            )
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating device")
            return self.async_show_form(
                step_id="user", data_schema=self.schema, errors={"base": "device_fail"},
            )

        name = f"AirThouch_{device['aircons'][self._selected_ac]['name']}"
        return self._async_get_entry({
                CONF_HOST: host,
                CONF_PORT: port
            })
 
    @property
    def schema(self):
        """Return current schema."""
        return vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT): int
            }
        )