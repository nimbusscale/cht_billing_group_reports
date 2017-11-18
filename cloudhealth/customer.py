class Customers:
    def __init__(self, client):
        self._client = client
        self._uri = 'v1/customers'

    @property
    def list(self):
        response = self._client.get(self._uri)
        return response['customers']

    @property
    def ids(self):
        response = self._client.get(self._uri)
        customer_list = response['customers']
        return {customer['name']: customer['id'] for customer in customer_list}


class Customer:

    def __init__(self, customer_client):
        self._client = customer_client
        self._uri = 'v1/customers/'



