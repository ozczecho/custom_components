from datetime import datetime, timedelta
import pytz
from urllib.request import Request, urlopen
import urllib
import logging
import re
import voluptuous as vol

# https://github.com/home-assistant/home-assistant/blob/855ed2b4e423147ce07fa69d6295ba561e6cb349/homeassistant/const.py
from homeassistant.const import CONF_ENTITIES, CONF_FILENAME, CONF_SCAN_INTERVAL, CONF_API_KEY, CONF_URL, CONF_TIME_ZONE
import subprocess
from homeassistant.helpers.event import track_time_interval
import homeassistant.helpers.config_validation as cv

DOMAIN = 'grafana_get'

HISTORY_DAYS = 'history_days'
IMAGE_HEIGHT = 'image_height'
IMAGE_WIDTH = 'image_width'
PANEL_ID = 'panel_id'
ORG_ID = 'organization_id'
BASE_DOWNLOAD_DIR = '/home/homeassistant/.homeassistant/downloads/'
DEFAULT_NAME = 'Chart'
DEFAULT_CONF_FILENAME = 'grafana.png'
DEFAULT_API_KEY = 'your_key'
DEFAULT_RENDER_URL = 'http://localhost/render'
DEFAULT_CONF_SCAN_INTERVAL = 60
DEFAULT_HISTORY_DAYS = 1
DEFAULT_IMAGE_HEIGHT = 500
DEFAULT_IMAGE_WIDTH = 1000
DEFAULT_PANEL_ID = 1
DEFAULT_ORG_ID = 1

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_API_KEY, DEFAULT_API_KEY): cv.string,
        vol.Required(CONF_URL, DEFAULT_RENDER_URL): cv.string,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_CONF_SCAN_INTERVAL): cv.positive_int,
        CONF_ENTITIES: vol.Schema({
            cv.string: vol.All({
                vol.Required(CONF_FILENAME, DEFAULT_CONF_FILENAME): cv.string,
                vol.Optional(HISTORY_DAYS, default=DEFAULT_HISTORY_DAYS): cv.positive_int,
                vol.Optional(IMAGE_HEIGHT, default=DEFAULT_IMAGE_HEIGHT): cv.positive_int,
                vol.Optional(IMAGE_WIDTH, default=DEFAULT_IMAGE_WIDTH): cv.positive_int,
                vol.Optional(PANEL_ID, default=DEFAULT_PANEL_ID): cv.string,
                vol.Optional(ORG_ID, default=DEFAULT_ORG_ID): cv.string
            })
        })
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    """Set up grafana_get component"""
    grafana = GrafanaGet(config)
    grafana.get_image()
    scan_interval = timedelta(seconds=config[DOMAIN].get(CONF_SCAN_INTERVAL))
    
    _LOGGER.info("Custom component {} is setup.".format(DOMAIN))
    
    def refresh(event_time):
        """Refresh"""
        _LOGGER.info("Refreshing Grafana Image")
        grafana.get_image()
 
    track_time_interval(hass, refresh, scan_interval)        

    # Initialization was successfull        
    return True

class GrafanaGet():
    """Object to get grafana rendered image"""

    def __init__(self, config):
        """Initialize"""
        self._api_key = config[DOMAIN].get(CONF_API_KEY)
        self._render_url = config[DOMAIN].get(CONF_URL)
        self._entities = config[DOMAIN][CONF_ENTITIES]

    def get_image(self):
        for entity in self._entities.items():
            image_name = entity[1].get(CONF_FILENAME)
            delta = timedelta(days = entity[1].get(HISTORY_DAYS))
            height = entity[1].get(IMAGE_HEIGHT)
            width = entity[1].get(IMAGE_WIDTH)
            tzName = entity[1].get(CONF_TIME_ZONE)
            panelId = entity[1].get(PANEL_ID)
            orgId = entity[1].get(ORG_ID)

            dt = pytz.utc.localize(datetime.utcnow())
            to_timestamp = 1000 * dt.timestamp()
            from_timestamp = 1000 * (dt - delta).timestamp()
            offset = dt.astimezone(tzName).strftime('%z')
            utc = urllib.parse.quote('UTC ' + offset[:3] + ':' + offset[-2:])

            url = '{0}?orgId={1}&panelId={2}&from={3}&to={4}&width={5}&height={6}&tz={7}' \
                        .format(self._render_url, orgId, panelId, from_timestamp, to_timestamp, width, height, utc)
            _LOGGER.info("Grafana render url is {}".format(url))

            req = Request(url)
            req.add_header('Authorization', 'Bearer {}'.format(self._api_key))
            result = urlopen(req).read()  

            f = open(BASE_DOWNLOAD_DIR + image_name, "wb")
            f.write(result)
            f.close()          