import aiohttp
import asyncio
import logging
import json.tool
import time

from datetime import timedelta
from aiohttp import ClientSession, ServerDisconnectedError
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=60)

AC_MODE_AUTO = 0
AC_MODE_HEAT = 1
AC_MODE_DRY = 2
AC_MODE_FAN = 3
AC_MODE_COOL = 4

AC_POWER_ON = 1
AC_POWER_OFF = 0

AC_FAN_MODE_QUIET = 0
AC_FAN_MODE_LOW = 1
AC_FAN_MODE_MEDIUM = 2
AC_FAN_MODE_HIGH = 3
AC_FAN_MODE_POWERFUL = 4
AC_FAN_MODE_AUTO = 5

AC_STATUS_OK = "OK"
AC_STATUS_ERROR = "ERROR"

ZONE_TEMPERATURE_TYPE_HIDE = 0
ZONE_TEMPERATURE_TYPE_USE_SENSOR = 1
ZONE_TEMPERATURE_TYPE_USE_TOUCH_PAD = 2
ZONE_TEMPERATURE_TYPE_USE_AVERAGE = 3

THERMOSTAT_MODE_AC = 0
THERMOSTAT_MODE_AVERAGE = 1
THERMOSTAT_MODE_AUTO = 2
THERMOSTAT_MODE_ZONE = 3

TEMPERATURE_INCREMENT = 1
TEMPERATURE_DECREMENT = -1

HTTP_GET = "GET"
HTTP_POST = "POST"

# Api calls
GET_VZDUCH_INFO = "/api/aircons"
POST_POWER_SWITCH = "/api/aircons/{0}/switch/{1}"
POST_AC_MODE = "/api/aircons/{0}/modes/{1}"
POST_AC_FAN_MODE = "/api/aircons/{0}/fanmodes/{1}"
POST_AC_TEMPERATURE = "/api/aircons/{0}/temperature/{1}"
POST_ZONE_TEMPERATURE = "/api/aircons/{0}/zones/{1}/temperature/{2}"
POST_ZONE_TOGGLE = "/api/aircons/{0}/zones/{1}/toggle"
POST_ZONE_SWITCH = "/api/aircons/{0}/zones/{1}/switch/{2}"

class Vzduch:
    """Api access to Vzduch.Dotek Net Server"""

    def __init__(self, session, host, port, timeout):
        self._session = session
        self._host = host
        self._port = port
        self._timeout = timeout
        self._available = False
        self._base_url = "http://{host}:{port}".format(host=self.host, port=self.port)
        _LOGGER.debug(f"[Vzduch] __init__  with [{self._base_url}]")

        self._selected_ac = 0 
        self._power = AC_POWER_OFF
        self._name = ''
        self._status = AC_STATUS_OK
        self._mode = AC_MODE_AUTO
        self._fan_mode = AC_FAN_MODE_LOW
        self._thermostat_mode = 0
        self._airtouch_id = ''
        self._touch_pad_temperature = 0
        self._desired_temperature = 0
        self._room_temperature = 0
        self._zones = []
        self._sensors = []

    async def fetch_get(self, command):
        """Send command via HTTP GET to Vzduch.Dotek Net server."""
        _LOGGER.debug("[Vzduch] Running fetch GET")
        async with self._session.get("{base_url}{command}".format(
            base_url=self._base_url, command=command)) as resp_obj:
            response = await resp_obj.text()
            if (resp_obj.status == 200 or resp_obj.status == 204):
                _LOGGER.debug("[Vzduch] Have a response")
                _LOGGER.debug(f"Host [{self._host}] returned HTTP status code [{resp_obj.status}] for GET command [{command}]")
                return response
            else:
                _LOGGER.error(f"Host [{self._host}] returned HTTP status code [{resp_obj.status}] for GET command [{command}]")
                return None

    async def fetch_post(self, command, data):
        """Send command via HTTP POST to Vzduch.Dotek Net server."""
        _LOGGER.debug("[Vzduch] Running fetch POST")
        async with self._session.post("{base_url}{command}".format(
            base_url=self._base_url, command=command), data=data) as resp_obj:
            response = await resp_obj.text()
            if (resp_obj.status == 200 or resp_obj.status == 204):
                _LOGGER.debug("[Vzduch] Have a response")
                return response
            else:
                _LOGGER.error(f"Host [{self._host}] returned HTTP status code [{resp_obj.status}] for POST command [{command}]")
                return None

    async def prep_fetch(self, verb, command, data = None, retries = 5):
        """ Prepare the session and command"""
        _LOGGER.debug("[Vzduch] Running prep_fetch")
        try:
            if self._session and not self._session.closed:
                if verb == HTTP_GET:
                    return await self.fetch_get(command)
                else:
                    return await self.fetch_post(command, data)
            async with aiohttp.ClientSession() as self._session:
                if verb == HTTP_GET:
                    return await self.fetch_get(command)
                else:
                    return await self.fetch_post(command, data)
        except ValueError:
            pass
        except ServerDisconnectedError as error:
            _LOGGER.debug(f"[Vzduch] Disconnected Error. Retry Count {retries}")
            if retries == 0:
                raise error
            return await self.prep_fetch(command, data, retries=retries - 1)

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self, **kwargs):
        """Get the latest status information from Vzduch.Dotek Net server"""

        _LOGGER.debug("[Vzduch] Doing async_update")
        response = await self.prep_fetch(HTTP_GET, GET_VZDUCH_INFO)
        self.set_properties(response)

    def set_properties(self, response):
        _LOGGER.debug("[Vzduch] Set properties start")

        if (response is not None):
            self._available = True
        else:
            _LOGGER.warning("[Vzduch] Response is None")
            self._available = False
            return

        data = json.loads(response)
        _LOGGER.debug(f"[Vzduch] Loaded response {data}")
        self._power = data["aircons"][self._selected_ac]["powerStatus"]
        self._name = data["aircons"][self._selected_ac]["name"]
        self._status = data["aircons"][self._selected_ac]["status"]
        self._mode = data["aircons"][self._selected_ac]["mode"]
        self._fan_mode = data["aircons"][self._selected_ac]["fanMode"]
        self._thermostat_mode = data["aircons"][self._selected_ac]["thermostatMode"]
        self._airtouch_id = data["aircons"][self._selected_ac]["airTouchId"]
        self._touch_pad_temperature= data["aircons"][self._selected_ac]["touchPadTemperature"]
        self._room_temperature = data["aircons"][self._selected_ac]["roomTemperature"]
        self._desired_temperature= data["aircons"][self._selected_ac]["desiredTemperature"]
        for zone_data in data["aircons"][self._selected_ac]["zones"]:
            existing_zone = list(filter(lambda x: x.id == zone_data["id"], self._zones))
            if existing_zone:
                existing_zone[0].update(zone_data)
            else:
                zone = Vzduch_Zone(zone_data)
                self._zones.append(zone)
            for sensor_data in zone_data["sensors"]:
                existing_sensor = list(filter(lambda x: x.id == sensor_data["id"], self._sensors))
                if existing_sensor:
                    existing_sensor[0].update(sensor_data)
                else:
                    sensor = Vzduch_Sensor(sensor_data)
                    self._sensors.append(sensor)
        _LOGGER.debug(f"[Vzduch] Set properties done. Zone count {len(self._zones)}")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_info(self):
        """Return a device description for device registry."""
        return {
            "manufacturer": "Polyaire",
            "model": "AirTouch 3",
            "name": self._name
        }

    @property
    def host(self):
        """Return the host address."""
        return self._host

    @property
    def port(self):
        """Return the host port."""
        return self._port

    @property
    def timeout(self):
        """Return the timeout."""
        return self._timeout

    @property
    def power(self):
        """Return the power status of the aircon unit."""
        return self._power

    @property
    def name(self):
        """Return the given name of the aircon unit"""
        return self._name

    @property
    def error_status(self):
        """Return the error status of the aircon unit."""
        return self._status

    @property
    def mode(self):
        """Return the current mode of the aircon unit (heat, cool etc)."""
        return self._mode

    @property
    def fan_mode(self):
        """Return the current fan mode of the aircon unit (low, medium, high)."""
        return self._fan_mode

    @property
    def thermostat_mode(self):
        """Return the current thermostat mode."""
        return self._thermostat_mode

    @property
    def thermostat_mode_desc(self):
        """Thermostat mode described"""
        if self.thermostat_mode == 0:
            return THERMOSTAT_MODE_AC
        elif self.thermostat_mode == (1 + len(self.zones)):
            return THERMOSTAT_MODE_AVERAGE
        elif self.thermostat_mode == (2 + len(self.zones)):
            return THERMOSTAT_MODE_AUTO
        else:
            temperature_zone = self.zones[len(self.zones) - 1]
            if temperature_zone.status == 1: # Is ON
                return THERMOSTAT_MODE_ZONE
            else:
                return THERMOSTAT_MODE_AC

    @property
    def airtouch_id(self):
        """Return the airtouch_id."""
        return self._airtouch_id

    @property
    def touch_pad_temperature(self):
        """Return the temperature of where the touchpad is."""
        return self._touch_pad_temperature

    @property
    def room_temperature(self):
        """Return the temperature of the main room."""
        return self._room_temperature

    @property
    def desired_temperature(self):
        """Return the desired temperature (Set Temperature)"""
        return self._desired_temperature

    @property
    def zones(self):
        """Return the zones created for this aircon"""
        return self._zones

    @property
    def sensors(self):
        """Return the sensors created for this aircon"""
        return self._sensors

    async def power_switch(self, to_state):
        """Switch unit on / off"""
        _LOGGER.debug(f"[Vzduch] power_switch to_state {to_state}")
        command = POST_POWER_SWITCH.format(self._selected_ac, to_state)
        response = await self.prep_fetch(HTTP_POST, command)
        self.set_properties(response)

    async def set_mode(self, to_mode):
        """Set the AC Mode (Heat / Cool, etc)"""
        _LOGGER.debug(f"[Vzduch] set_mode to_mode {to_mode}")
        command = POST_AC_MODE.format(self._selected_ac , to_mode)
        response = await self.prep_fetch(HTTP_POST, command)
        self.set_properties(response)

    async def set_fan_mode(self, to_mode):
        """Set the AC Fan Mode (Low / Med, High)"""
        _LOGGER.debug(f"[Vzduch] set_fan_mode to_mode {to_mode}")
        command = POST_AC_FAN_MODE.format(self._selected_ac, to_mode)
        response = await self.prep_fetch(HTTP_POST, command)
        self.set_properties(response)

    async def set_temperature(self, to_temperature):
        """Set the desired temperature"""
        _LOGGER.debug(f"[Vzduch] set_temperature to_temperature {to_temperature} current desired {self.desired_temperature}")
        inc_dec = (TEMPERATURE_INCREMENT if to_temperature >= self.desired_temperature else TEMPERATURE_DECREMENT)
        command = POST_AC_TEMPERATURE.format(self._selected_ac, inc_dec)
        response = await self.prep_fetch(HTTP_POST, command)
        self.set_properties(response)

    async def set_temperature_thermostat_mode(self, to_temperature):
        """Set the desired temperature"""
        _LOGGER.debug(f"[Vzduch] set_temperature_thermostat_mode to_temperature {to_temperature}")
        if self.thermostat_mode_desc == THERMOSTAT_MODE_ZONE:
            temperature_zone = self.zones[len(self.zones) - 1]
            if temperature_zone is not None:
                await self.set_zone_temperature(temperature_zone.id, to_temperature)
            else:
                _LOGGER.warning(f"[Vzduch] Cannot set set_zone_temperature - zone not available")
        else:
            await self.set_temperature(to_temperature)

    async def zone_toggle(self, zone_id):
        """Switch zone on / off"""
        _LOGGER.debug(f"[Vzduch] zone_toggle zone_id {zone_id}")
        command = POST_ZONE_TOGGLE.format(self._selected_ac, zone_id)
        response = await self.prep_fetch(HTTP_POST, command)
        self.set_properties(response)

    async def zone_switch(self, zone_id, to_state):
        """Switch zone on / off"""
        _LOGGER.debug(f"[Vzduch] zone_switch zone_id {zone_id}  to_state {to_state}")
        command = POST_ZONE_SWITCH.format(self._selected_ac, zone_id, to_state)
        response = await self.prep_fetch(HTTP_POST, command)
        self.set_properties(response)

    async def set_zone_temperature(self, zone_id, to_temperature):
        """Set the desired temperature for a given zone"""
        _LOGGER.debug(f"[Vzduch] set_zone_temperature to_temperature {to_temperature}")
        selected_zone = self.zones[zone_id]
        if selected_zone is None:
            _LOGGER.warning(f"[Vzduch] Selected Zone with Id {zone_id} not found")
            return

        _LOGGER.debug(f"[Vzduch] Zone with Id {zone_id} current desired temperature {selected_zone.desired_temperature}")
        inc_dec = (TEMPERATURE_INCREMENT if to_temperature >= selected_zone.desired_temperature else TEMPERATURE_DECREMENT)
        command = POST_ZONE_TEMPERATURE.format(self._selected_ac, zone_id, inc_dec)
        response = await self.prep_fetch(HTTP_POST, command)
        self.set_properties(response)
        return selected_zone.desired_temperature

class Vzduch_Zone:
    """ A Zone """
    def __init__(self, zone_data):
        self._id = zone_data["id"]
        self._name = zone_data["name"]
        self.update(zone_data)

    def update(self, zone_data):
        """Once a zone is created a subset of its properties are kept up to date"""
        self._status = zone_data["status"]
        self._fan_value = zone_data["fanValue"]
        self._is_spill = zone_data["isSpill"]
        self._desired_temperature = zone_data["desiredTemperature"]
        self._zone_temperature_type = zone_data["zoneTemperatureType"]
        self._sensors = []
        for sensor_data in zone_data["sensors"]:
            sensor = Vzduch_Sensor(sensor_data)
            self._sensors.append(sensor)

    @property
    def id(self):
        """Returns the id for the zone"""
        return self._id

    @property
    def name(self):
        """Returns the name for the zone"""
        return self._name

    @property
    def status(self):
        """Returns the zone status (on / off)"""
        return self._status

    @property
    def fan_value(self):
        """Returns the zone fan value"""
        return self._fan_value

    @property
    def is_spill(self):
        """Returns whether the zone is used as spill"""
        return self._is_spill

    @property
    def desired_temperature(self):
        """Returns the zone desired temperature"""
        return self._desired_temperature

    @property
    def zone_temperature_type(self):
        """Returns how the temperature is calculated or used within the zone"""
        return self._zone_temperature_type

    @property
    def sensors(self):
        """Returns all sensors registered in the zone"""
        return self._sensors

class Vzduch_Sensor:
    """ A Sensor in a Zone """
    def __init__(self, sensor_data):
        self._id = sensor_data["id"]
        self._is_available = sensor_data["isAvailable"]
        self.update(sensor_data)

    def update(self, sensor_data):
        """Once a sensor is created a subset of its properties are kept up to date"""
        self._is_low_battery = sensor_data["isLowBattery"]
        self._temperature = sensor_data["temperature"]

    @property
    def id(self):
        """Returns the id for the sensor"""
        return self._id

    @property
    def is_available(self):
        """Return whether the sensor is available or not"""
        return self._is_available

    @property
    def is_low_battery(self):
        """Return the battery status for the sensor"""
        return self._is_low_battery

    @property
    def temperature(self):
        """Return the temperature for the sensor"""
        return self._temperature