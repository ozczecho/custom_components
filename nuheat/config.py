import nuheat.const as const

class Config:
    _auth_url_part = "/authenticate/user"
    _thermostat_url_part = "/thermostat"

    _api_url  = None
    _request_headers = None

    def __init__(self, region):
        if region == "AU":
            self._api_url = const.API_URL_AU
        elif region == "USA":
            self._api_url = const.API_URL_USA
        else:
            self._api_url = null

        self._request_headers = {
            "content-type": "application/x-www-form-urlencoded",
            "accept": "application/json",
            "dnt": "1",
            "origin": self._api_url
        }

    @property
    def api_url(self):
        """
        Return the api url
        """
        return self._api_url

    @property
    def auth_url(self):
        """
        Return the auth url
        """
        return self._api_url + self._auth_url_part

    @property
    def thermostat_url(self):
        """
        Return the thermostat url
        """
        return self._api_url + self._thermostat_url_part

    @property
    def request_headers(self):
        """
        Return the api request headers
        """
        return self._request_headers


