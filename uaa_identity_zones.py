"""
Python client for Cloud Foundry UAA Identity Zones API
Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#identity-zones
"""


import requests


class UAAIdentityZonesClient:
    """
    A client for interacting with the UAA Identity Zones API.
    """

    def __init__(self, base_url: str, token: str):
        """
        Initializes the UAAIdentityZonesClient.

        Args:
            base_url: The base URL of the UAA server.
            token: The OAuth2 bearer token for authentication.
        """
        self.base_url = base_url.rstrip('/')
        self.token = token

    def _headers(self) -> dict:
        """
        Constructs the request headers.

        Returns:
            A dictionary of request headers.
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def create_an_identity_zone(
        self,
        id: str,
        subdomain: str,
        name: str,
        description: str
    ) -> dict:
        """
        Creates a new identity zone.

        Args:
            id: Unique identifier for the identity zone.
            subdomain: The subdomain for the new identity zone.
            name: The name of the new identity zone.
            description: A description for the new identity zone.

        Returns:
            The response from the UAA server.
        """
        url = f"{self.base_url}/identity-zones"
        payload = {
            "id": id,
            "subdomain": subdomain,
            "name": name,
            "description": description,
        }
        try:
            response = requests.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"error": "UAA server is not running."}
