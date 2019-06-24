import logging
import re
import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.const import CONF_SCAN_INTERVAL 
import homeassistant.loader as loader
import subprocess
from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
import homeassistant.helpers.config_validation as cv

DOMAIN = 'temper2_mqtt'

DEPENDENCIES = ['mqtt']

HID_QUERY_SCRIPT = '/home/homeassistant/.homeassistant/custom_components/hid-query'
MAX_TEMP = 90.0
TOPIC = 'topic'
DEFAULT_TOPIC = "house/temperature"
DEFAULT_CONF_SCAN_INTERVAL = 60

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(TOPIC, DEFAULT_TOPIC): cv.string,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_CONF_SCAN_INTERVAL): cv.positive_int
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up Temper2 MQTT component"""
    topic = config[DOMAIN].get(TOPIC)
    scan_interval = timedelta(seconds=config[DOMAIN].get(CONF_SCAN_INTERVAL))
    mqtt = hass.components.mqtt

    #Need to get the device id of the Tempre@ device: 0001:0004:01
    result = subprocess.run([HID_QUERY_SCRIPT, '-e'], stdout=subprocess.PIPE)
    #_LOGGER.warn("-e result {}".format(result.stdout.decode('utf-8')))
    deviceId = ""
    deviceIds = re.search(r"(.*?01) : 413d:2107.*", result.stdout.decode('utf-8'), re.M|re.I)
    if deviceIds:
        deviceId = deviceIds.group(1)
        _LOGGER.warn("Temper2 - Found DeviceId {}".format(deviceId))
    else:
        _LOGGER.warn("NO MATCH")
        raise Exception("No 413d:2107 device found.")

    _LOGGER.info("Custom component {} is setup.".format(DOMAIN))

    def set_state_service(call):
        """Service to send a message."""
        msg = '{{"temperature":{}}}'.format(call.data.get('new_state'))  
        _LOGGER.warn("Publish " + msg)
        mqtt.publish(topic, msg)

    def refresh(event_time):
        """Refresh"""
        temp_parts = get_Temper2Reading()
        current_temperature = calc_Temperature(temp_parts)
        if current_temperature < MAX_TEMP:
            msg = '{{"temperature":{}}}'.format(current_temperature)
            mqtt.publish(topic, msg)
            _LOGGER.info("Published " + msg)
        else:
            # Sometimes the unit returns crazy values 328 deg celcius, for now we just log
            _LOGGER.warn("Wrong Temperature reading [{}]".format(current_temperature))

    def get_Temper2Reading():
        result = subprocess.run([HID_QUERY_SCRIPT, deviceId,'0x01','0x80','0x33','0x01','0x00','0x00','0x00','0x00'], stdout=subprocess.PIPE)
        # _LOGGER.warn("Publish " + result.stdout.decode('utf-8')) '0001:0004:01'
        parts = result.stdout.decode('utf-8').split('\n')
        while '' in parts:
            parts.remove('')
        return parts

    def calc_Temperature(parts):
        temperature_line = parts[len(parts) - 1].split(' ')
        # list looks like ['\t', '80', '01', '0a', '73', '', '', '4e', '20', '00', '00']
        # we want item 3 & 4 ('0a', '73')

        temp = ((int(temperature_line[3], 16) << 8 ) + int(temperature_line[4], 16)) / 100
        return temp       

    track_time_interval(hass, refresh, scan_interval)        

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'set_state', set_state_service)

    # Initialization was successfull        
    return True
