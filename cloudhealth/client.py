import logging

from cloudhealth.customer import Customers
from cloudhealth.perspective import Perspectives, Perspective
from cloudhealth.report import CostHistory

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
        print(response.url)
        if response.status_code != 200:
            raise RuntimeError(
                'Request to {} failed! (HTTP Error Code: {})'.format(
                    url, response.status_code))
        return response.json()

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, param_dict):
        self._params = param_dict

    def add_param(self, param):
        params = self.params
        params.update(param)
        self.params = params


class CloudHealth:

    def __init__(self, api_key, client_api_id=None):
        self._client = HTTPClient(DEFAULT_CLOUDHEALTH_API_URL,
                                  api_key=api_key,
                                  client_api_id=client_api_id)

    @property
    def customers(self):
        return Customers(self._client)

    @property
    def perspectives(self):
        return Perspectives(self._client)

    def get_perspective(self, perspective_id):
        return Perspective(self._client, perspective_id)

    @property
    def cost_history(self):
        return CostHistory(self._client,
                           '2954937501729',
                           '2954937520673')



