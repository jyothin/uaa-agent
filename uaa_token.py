"""
Python client for the UAA API endpoints for tokens.
"""


import requests


class UAAClientCredentialsGrantClient:
    """
    A client for interacting with the UAA's client credentials grant functionality.
    """

    def __init__(self, base_url: str):
        """
        Initializes the UAAClientCredentialsGrantClient.

        :param base_url: The base URL of the UAA server.
        """
        self.base_url = base_url.rstrip('/')

    def create_without_authorization(
        self,
        client_id: str,
        client_secret: str,
        token_format: str,
        scope: list[str]
    ) -> dict:
        """
        Retrieves a token using the client credentials grant type without an Authorization header.

        Corresponds to the UAA API documentation:
        https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#without-authorization

        :param client_id: The ID of the client.
        :param client_secret: The secret of the client.
        :param token_format: Optional. Can be 'opaque' or 'jwt'.
        :param scope: Optional. A list of scopes to request for the token.
        :return: A dictionary containing the token information.
        """
        url = f"{self.base_url}/oauth/token"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        if token_format:
            data['token_format'] = token_format
        if scope:
            data['scope'] = ' '.join(scope)

        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {"error": "UAA server is not running."}
