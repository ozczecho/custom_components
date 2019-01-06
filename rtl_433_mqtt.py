"""
A custom component for Home Assistant
A 433 to HA bridge.
Subscribes to all messages published on the `/all` topic. Then for selected messages it publishes those to Home Assistant (DEFAULT: home/rtl_433)
Currently listens for Doorbell, Oreggon Scientific Temperature sensor, Fine Offset WH24 weather station, Prologue sensor (cheap chinese temperature sensors)
"""

import logging
import re
import voluptuous as vol
import json

from homeassistant.const import CONF_SCAN_INTERVAL 
import homeassistant.loader as loader
import subprocess
from datetime import timedelta
from homeassistant.helpers.event import track_time_interval
import homeassistant.helpers.config_validation as cv

DOMAIN = 'rtl_433_mqtt'

DEPENDENCIES = ['mqtt']

TOPIC = "topic"
DEFAULT_TOPIC = "home/rtl_433"
_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(TOPIC, DEFAULT_TOPIC): cv.string
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up rtl 433 mqtt component"""
    mqtt = loader.get_component(hass, 'mqtt')
    topic = config[DOMAIN].get(TOPIC)
    _LOGGER.info("Custom component {} is setup.".format(DOMAIN))

    def on_msg_received(topic, payload, qos):
        """Handle home/rtl_433 messages"""
        _LOGGER.info("Message received")
        msg = json.loads(payload)
        pub_topic = config[DOMAIN].get(TOPIC)
        if msg.get("model","<null>") == "doorbell":
            # "time" : "2018-09-29 15:50:47", "model" : "doorbell", "count" : 3, "num_rows" : 5, "rows" : [{"len" : 0, "data" : ""}, {"len" : 24, "data" : "000000"},
            _LOGGER.info("Doorbell")
            
            response = '{{"doorbellRing":true,"lastRing":"{0}"}}'.format(msg["time"])
            mqtt.publish(hass, pub_topic + "/door" , response)

        elif msg.get("brand","<null>") == "OS":
            _LOGGER.info("Oregon Sc")
            # "battery" : "LOW", "temperature_C" : 21.500, "humidity" : 33
            response = '{{"temperature":{0},"humidity":{1},"battery":"{2}"}}'.format(msg["temperature_C"], msg["humidity"], msg["battery"])
            
            mqtt.publish(hass, pub_topic + "/temperature/os", response)

        elif msg.get("model","<null>") == "Prologue sensor":
            _LOGGER.info("Prologue sensor")
            # {"time" : "2019-01-02 12:31:17", "model" : "Prologue sensor", "id" : 5, "rid" : 210, "channel" : 1, "battery" : "OK", "button" : 0, "temperature_C" : 28.000, "humidity" : 57}
            response = '{{"temperature":{0},"humidity":{1},"battery":"{2}"}}'.format(msg["temperature_C"], msg["humidity"], msg["battery"])
            
            mqtt.publish(hass, '{0}/temperature/rid/{1}'.format(pub_topic, msg["rid"]), response)

        elif msg.get("model","<null>") == "Fine Offset WH24": 
            # "temperature_C" : 16.400, "humidity" : 52, "wind_dir_deg" : 19, "wind_speed_ms" : 0.840, "gust_speed_ms" : 1.120, "rainfall_mm" : 313.500, "uv" : 933, "uvi" : 2, "light_lux" : 14964.700, "battery" : "OK", "mic" : "CRC"}
            response = '{{"temperature":{0},"humidity":{1},"battery":"{2}","windDirectionDegrees":{3},"windSpeedms":{4},"gustSpeedms":{5}}}' \
                .format(msg["temperature_C"], msg["humidity"], msg["battery"], msg["wind_dir_deg"], msg["wind_speed_ms"], msg["gust_speed_ms"])
            
            _LOGGER.info("Outside {}".format(response))
            mqtt.publish(hass, pub_topic + "/temperature/fo", response)   

    _LOGGER.warn("Subscribing to topic {}/all".format(topic))
    mqtt.subscribe(hass, topic + "/all", on_msg_received)

    # Initialization was successfull        
    return True                


