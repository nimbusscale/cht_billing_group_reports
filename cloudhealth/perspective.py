class Perspectives:
    def __init__(self, client):
        self._client = client
        self._uri = 'v1/perspective_schemas/'

    @property
    def list(self):
        response = self._client.get(self._uri)
        return response

    @property
    def active(self):
        # list only active perspectives
        self._client.add_param({'active_only': 'true'})
        response = self._client.get(self._uri)
        return response


class Perspective:

    def __init__(self, client, perspective_id):
        self._client = client
        self._uri = 'v1/perspective_schemas/' + perspective_id

    @property
    def config(self):
        response = self._client.get(self._uri)
        return response

    @property
    def groups(self):
        response = self._client.get(self._uri)
        groups_dict_list = response['schema']['constants'][0]['list']
        return {group['name']: group['ref_id'] for group in groups_dict_list}
