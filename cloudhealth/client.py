import logging

from cloudhealth.customers import Customers

import requests

logger = logging.getLogger()

DEFAULT_CLOUDHEALTH_API_URL = 'https://chapi.cloudhealthtech.com/'


class HTTPClient:
    def __init__(self, endpoint, api_key, client_api_id=None):
        self._endpoint = endpoint
        self._headers = {'Content-type': 'application/json'}
        self._params = {'api_key': api_key,
                        'client_api_id': client_api_id}

    def get(self, uri):
        url = self._endpoint + uri
        response = requests.get(url,
                                params=self._params,
                                headers=self._headers)
        if response.status_code != 200:
            raise RuntimeError(
                'Request to {} failed! (HTTP Error Code: {})'.format(
                    url, response.status_code))
        return response.json()


class CloudHealth:

    def __init__(self, api_key, client_api_id=None):
        self._client = HTTPClient(DEFAULT_CLOUDHEALTH_API_URL,
                                  api_key=api_key,
                                  client_api_id=client_api_id)
        self._customers = Customers(self._client)

    @property
    def customers(self):
        return self._customers

