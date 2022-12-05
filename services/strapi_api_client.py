import json
import requests

from conf import settings


class StrapiApiClient:
    def __init__(self):
        self.api_url = "https://strapi-production-2328.up.railway.app/api"

    def get_community(self, name: str):
        response = requests.get(
            url=self.api_url + f"/communities?filters[name][$eqi]={name}",
            headers={
                "Authorization": f"Bearer {settings.STRAPI_API_KEY}"
            }
        )
        return response.json()

    def create_community(self, data: dict):
        try:
            response = requests.post(
                url=f"{self.api_url}/communities",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.STRAPI_API_KEY}"
                },
                params={"populate": "communities"},
                data=json.dumps({"data": data}),
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"Error connecting: {e}")
        except requests.exceptions.Timeout as e:
            print(f"Timeout error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Unexpected error: {e}")

    def delete_community(self, community_id: int):
        try:
            response = requests.delete(
                url=self.api_url + f"/communities/{community_id}",
                headers={
                    "Authorization": f"Bearer {settings.STRAPI_API_KEY}"
                }
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"Error connecting: {e}")
        except requests.exceptions.Timeout as e:
            print(f"Timeout error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Unexpected error: {e}")

        return response.json()
