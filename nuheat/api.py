import logging
import requests
from nuheat.config import Config
from nuheat.thermostat import NuHeatThermostat

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class NuHeat(object):

    def __init__(self, region, username, password, session_id=None):
        """
        Initialize a NuHeat API session
        :param region: NuHeat region (currently USA or AU)
        :param username: NuHeat username
        :param password: NuHeat password
        :param session_id: A Session ID token to re-use to avoid re-authenticating
        """
        self.config = Config(region)
        self.username = username
        self.password = password
        self._session_id = session_id

    def __repr__(self):
        return "<NuHeat username='{}'>".format(self.username)

    def authenticate(self):
        """
        Authenticate against the NuHeat API
        """
        if self._session_id:
            _LOGGER.debug("Using existing NuHeat session")
            return

        _LOGGER.debug("Creating NuHeat session")
        post_data = {
            "Email": self.username,
            "Password": self.password,
            "Application": "0"
        }

        data = self.request(self.config.auth_url,
                            method="POST", data=post_data)
        session_id = data.get("SessionId")
        if not session_id:
            raise Exception("Authentication error")

        self._session_id = session_id

    def get_thermostat(self, serial_number):
        """
        Get a thermostat object by serial number

        :param serial_number: The serial number / ID of the desired thermostat
        """
        return NuHeatThermostat(self, serial_number)

    def request(self, url, method="GET", data=None, params=None, retry=True):
        """
        Make a request to the NuHeat API

        :param url: The URL to request
        :param method: The type of request to make (GET, POST)
        :param data: Data to be sent along with POST requests
        :param params: Querystring parameters
        :param retry: Attempt to re-authenticate and retry request if necessary
        """
        headers = self.config._request_headers

        if params and self._session_id:
            params['sessionid'] = self._session_id

        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, params=params, data=data)

        # Handle expired sessions
        if response.status_code == 401 and retry:
            _LOGGER.warn("NuHeat APIrequest unauthorized [401]. Try to re-authenticate.")
            self._session_id = None
            self.authenticate()
            return self.request(url, method=method, data=data, params=params, retry=False)

        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            # No JSON object
            return response
