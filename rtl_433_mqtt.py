import logging
import re
import voluptuous as vol
import json
import custom_components.elect_calc as elector

from homeassistant.components import mqtt
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_TIME_ZONE
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
        vol.Required(TOPIC, DEFAULT_TOPIC): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up rtl 433 mqtt component"""
    topic = config[DOMAIN].get(TOPIC)
    timezone = config.get(CONF_TIME_ZONE, hass.config.time_zone)
    mqtt = hass.components.mqtt

    _LOGGER.warn("TZ *** {} is setup.".format(timezone))
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
            mqtt.publish(pub_topic + "/door" , response)
        elif msg.get("model", "<null>") == "Efergy e2 CT":
            _LOGGER.info("Efergy")
            try:
                kw = 0.24 * float(msg["current"])
                efergy = elector.calc(msg["time"], "{0}".format(timezone))

                response = '{{"current":{0},"kW":{1},"interval":{2},"time":"{3}","chargeType":"{4}","charge":{5}}}'.format(
                    msg["current"], kw, msg["interval"], msg["time"], efergy.Type, efergy.Charge)

                mqtt.publish(pub_topic + "/energy", response)
            except ValueError as e:
                _LOGGER.warn("Error in processing efergy {0}".format(e))
                return

        elif msg.get("brand","<null>") == "OS":
            _LOGGER.info("Oregon Sc")
            # {"time" : "2019-06-24 04:36:40", "brand" : "OS", "model" : "THGR122N", "id" : 233, "channel" : 1, "battery" : "OK", "temperature_C" : 16.000, "humidity" : 54}
            if (msg["model"] == "THGR122N" and msg["id"] == 233):
                response = '{{"temperature":{0},"humidity":{1},"battery":"{2}"}}'.format(msg["temperature_C"], msg["humidity"], msg["battery"])
                mqtt.publish(pub_topic + "/temperature/os", response)
            else:
                _LOGGER.warn("Received unrecognised message {0} {1}".format(msg["brand"], msg["model"]))

        elif msg.get("model","<null>") == "Prologue sensor":
            _LOGGER.info("Prologue sensor")
            # {"time" : "2019-01-02 12:31:17", "model" : "Prologue sensor", "id" : 5, "rid" : 210, "channel" : 1, "battery" : "OK", "button" : 0, "temperature_C" : 28.000, "humidity" : 57}
            response = '{{"temperature":{0},"humidity":{1},"battery":"{2}"}}'.format(msg["temperature_C"], msg["humidity"], msg["battery"])
            
            mqtt.publish('{0}/temperature/rid/{1}'.format(pub_topic, msg["rid"]), response)

        elif msg.get("model","<null>") == "Fine Offset WH24": 
            # "temperature_C" : 16.400, "humidity" : 52, "wind_dir_deg" : 19, "wind_speed_ms" : 0.840, "gust_speed_ms" : 1.120, "rainfall_mm" : 313.500, "uv" : 933, "uvi" : 2, "light_lux" : 14964.700, "battery" : "OK", "mic" : "CRC"}
            response = '{{"temperature":{0},"humidity":{1},"battery":"{2}","windDirectionDegrees":{3},"windSpeedms":{4},"gustSpeedms":{5}}}' \
                .format(msg["temperature_C"], msg["humidity"], msg["battery"], msg["wind_dir_deg"], msg["wind_speed_ms"], msg["gust_speed_ms"])
            
            _LOGGER.info("Outside {}".format(response))
            mqtt.publish(pub_topic + "/temperature/fo", response) 

        elif msg.get("model", "<null>") == "Kerui Security":
            # {"time" : "2019-02-06 00:05:09", "model" : "Kerui PIR Sensor", "id" : 7962, "data" : "0xa (PIR)"
            response = '{"message":"motion detected"}'
            
            mqtt.publish('{0}/pir/id/{1}'.format(pub_topic, msg["id"]), response)              

    _LOGGER.warn("Subscribing to topic {}/all".format(topic))
    mqtt.subscribe(topic + "/all", on_msg_received)

    # Initialization was successfull        
    return True                

