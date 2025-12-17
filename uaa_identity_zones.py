"""
Python client for Cloud Foundry UAA Identity Zones API (version 78.5.0)
Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#identity-zones
"""


import requests

HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_NOT_FOUND = 404


def set_token_for_uaa_identity_zones_client(token: str) -> None:
    """Set the token for the UAAIdentityZonesClient class variable."""
    UAAIdentityZonesClient.token = token

class UAAIdentityZonesClient:
    """
    A client for interacting with the UAA Identity Zones API.
    """

    token = "<dummy token>"

    def __init__(self, base_url: str):
        """
        Initializes the UAAIdentityZonesClient.

        Args:
            base_url: The base URL of the UAA server.
        """
        self.base_url = base_url.rstrip('/')


    def _headers(self) -> dict:
        """
        Constructs the request headers.

        Returns:
            A dictionary of request headers.
        """
        return {
            'Authorization': f'Bearer {UAAIdentityZonesClient.token}',
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
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == HTTP_STATUS_UNAUTHORIZED:
                return {"error": "Unauthorized: Invalid or expired token."}
            raise e
        except requests.exceptions.ConnectionError:
            return {"error": "UAA server is not running."}

    def get_identity_zone(self, zone_id: str) -> dict:
        """
        Retrieves an identity zone by its ID.

        Args:
            zone_id: The ID of the identity zone to retrieve.

        Returns:
            The response from the UAA server.
        """
        url = f"{self.base_url}/identity-zones/{zone_id}"
        try:
            response = requests.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == HTTP_STATUS_UNAUTHORIZED:
                return {"error": "Unauthorized: Invalid or expired token."}
            if e.response.status_code == HTTP_STATUS_NOT_FOUND:
                return {"error": f"Identity zone with ID '{zone_id}' not found."}
            raise e
        except requests.exceptions.ConnectionError:
            return {"error": "UAA server is not running."}

    def get_all_identity_zones(self) -> dict:
        """
        Retrieves all identity zones.

        Returns:
            The response from the UAA server.
        """
        url = f"{self.base_url}/identity-zones"
        try:
            response = requests.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == HTTP_STATUS_UNAUTHORIZED:
                return {"error": "Unauthorized: Invalid or expired token."}
            raise e
        except requests.exceptions.ConnectionError:
            return {"error": "UAA server is not running."}

    def update_identity_zone(
        self,
        zone_id: str,
        subdomain: str,
        name: str,
        description: str
    ) -> dict:
        """
        Updates an existing identity zone.

        Args:
            zone_id: The ID of the identity zone to update.
            subdomain: The updated subdomain for the identity zone.
            name: The updated name of the identity zone.
            description: The updated description for the identity zone.

        Returns:
            The response from the UAA server.
        """
        url = f"{self.base_url}/identity-zones/{zone_id}"
        payload = {
            "id": zone_id,
            "subdomain": subdomain,
            "name": name,
            "description": description,
        }
        try:
            response = requests.put(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == HTTP_STATUS_UNAUTHORIZED:
                return {"error": "Unauthorized: Invalid or expired token."}
            if e.response.status_code == HTTP_STATUS_NOT_FOUND:
                return {"error": f"Identity zone with ID '{zone_id}' not found."}
            raise e
        except requests.exceptions.ConnectionError:
            return {"error": "UAA server is not running."}
