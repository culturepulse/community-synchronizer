import json
from json import JSONEncoder
from typing import Union, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from services.strapi.errors import ApiException


class StrapiApiClient:
    def __init__(self, api_url: str, token: str, timeout: int = 30):
        self._api_url = api_url
        self._token = token
        self._timeout = timeout

    def get_community(self, name: str):
        response = self._request(
            method='GET',
            endpoint_url=f"{self._api_url}/communities?filters[name][$eqi]={name}",
            query={'filters[name][$eqi]': name}
        )
        return response

    def create_community(self, data: dict):
        response = self._request(
            method='POST',
            endpoint_url=f"{self._api_url}/communities",
            query={'populate': 'communities'},
            payload={'data': data}
        )
        return response

    def delete_community(self, community_id: int):
        response = self._request(
            method='DELETE',
            endpoint_url=f"{self._api_url}/communities/{community_id}"
        )
        return response

    def _request(
            self, method: str, endpoint_url: str, payload: dict = None, query: dict = None, parse: bool = True
    ) -> Union[str, Dict]:
        request = Request(
            method=method,
            url=endpoint_url,
            headers={"Authorization": self._token}
        )

        if payload and isinstance(payload, dict):
            request.data = json.loads(json.dumps(payload, cls=JSONEncoder))
            request.headers['Content-Type'] = 'application/json'

        if query and isinstance(query, dict):
            request.params = query

        try:
            response = urlopen(request, timeout=self._timeout)
        except HTTPError as error:
            raise ApiException(request, f'{error.status} - {error.reason}')
        except URLError as error:
            raise ApiException(request, error.reason)
        else:
            if parse:
                try:
                    data = json.loads(response.read())
                except json.JSONDecodeError as error:
                    raise ApiException(request, error.msg)
            else:
                data = response.read()

            return data
