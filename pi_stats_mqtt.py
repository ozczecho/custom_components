"""
A custom component for Home Assistant
Uses the vcgencmd command to get the temperature reading of the device
The temperature is then published on a MQTT message bus.
"""

import logging
import re
import voluptuous as vol

from homeassistant.const import CONF_SCAN_INTERVAL 
import homeassistant.loader as loader
import subprocess
from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
import homeassistant.helpers.config_validation as cv

DOMAIN = 'pi_stats_mqtt'

DEPENDENCIES = ['mqtt']

VCGENCMD_SCRIPT = '/opt/vc/bin/vcgencmd'
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
    """Set up pi stats MQTT component"""
    mqtt = loader.get_component(hass, 'mqtt')
    topic = config[DOMAIN].get(TOPIC)
    scan_interval = timedelta(seconds=config[DOMAIN].get(CONF_SCAN_INTERVAL))

    _LOGGER.info("Custom component {} is setup.".format(DOMAIN))

    def set_state_service(call):
        """Service to send a message."""
        msg = '{{"temperature":{}}}'.format(call.data.get('new_state'))  
        _LOGGER.warn("Publish " + msg)
        mqtt.publish(hass, topic, msg)

    def refresh(event_time):
        """Refresh"""
        result = subprocess.run([VCGENCMD_SCRIPT, 'measure_temp'], stdout=subprocess.PIPE)
        # _LOGGER.warn("Publish " + result.stdout.decode('utf-8')) '0001:0004:01'
        # result is temp=45.6'C, so need to grab the number only
        msg = '{{"temperature":{}}}'.format(convert_result(result.stdout.decode('utf-8')))
        mqtt.publish(hass, topic, msg)
        _LOGGER.info("Published " + msg)

    def convert_result(result):
        temp_string = result.split("=")
        return temp_string[1].split("'")[0]


    track_time_interval(hass, refresh, scan_interval)        

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'set_state', set_state_service)

    # Initialization was successfull        
    return True
