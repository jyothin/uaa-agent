"""
Python client for Cloud Foundry UAA Server Information API (version 78.5.0)
Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#server-information
"""
import requests
from typing import Optional

class UAAServerInformationClient:
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.token = token

    def _headers(self):
        headers = {'Accept': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def get_server_information(self) -> dict:
        """
        GET /info
        Returns UAA server information.
        Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#server-information
        """
        url = f"{self.base_url}/info"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def get_openid_configuration(self) -> dict:
        """
        GET /.well-known/openid-configuration
        Returns OpenID Connect Discovery information.
        Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#openid-connect-discovery
        """
        url = f"{self.base_url}/.well-known/openid-configuration"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def create_passcode(self) -> dict:
        """
        POST /passcode
        Creates a new one-time passcode for the authenticated user.
        Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#passcode
        """
        url = f"{self.base_url}/passcode"
        response = requests.post(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def get_passcode(self) -> dict:
        """
        GET /passcode
        Retrieves the current one-time passcode for the authenticated user (if available).
        Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#passcode
        """
        url = f"{self.base_url}/passcode"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def get_auto_login(self) -> dict:
        """
        GET /autologin
        Retrieves auto-login information for the authenticated user.
        Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#auto-login
        """
        url = f"{self.base_url}/autologin"
        headers = self._headers()
        headers['Content-Type'] = 'application/json'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def create_auto_login(self, username: str, password: str) -> dict:
        """
        POST /autologin
        Creates auto-login for the authenticated user.
        Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#auto-login
        """
        url = f"{self.base_url}/autologin"
        headers = self._headers()
        headers['Content-Type'] = 'application/json'
        data = {'username': username, 'password': password}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def perform_login(self, code: str, client_id: str) -> dict:
        """
        GET /autologin
        Performs a login action for the client.
        Docs: https://docs.cloudfoundry.org/api/uaa/version/78.5.0/index.html#perform-login
        """
        url = f"{self.base_url}/autologin"
        headers = self._headers()
        data = {'code': code, 'client_id': client_id}
        response = requests.get(url, headers=headers, params=data)
        response.raise_for_status()
        return response.json()

# Example usage:
# client = UAAServerInformationClient(base_url="https://uaa.example.com", token="YOUR_ACCESS_TOKEN")
# server_info = client.get_server_information()
# print("Server Information:", server_info)
#
# openid_config = client.get_openid_configuration()
# print("OpenID Configuration:", openid_config)
#
# passcode = client.create_passcode()
# print("Created Passcode:", passcode)
#
# current_passcode = client.get_passcode()
# print("Current Passcode:", current_passcode)
#
# auto_login_info = client.get_auto_login()
# print("Auto-Login Info:", auto_login_info)
#
# created_auto_login = client.create_auto_login(username, password)
# print("Created Auto-Login:", created_auto_login)
#
# perform_login = client.perform_login(code, client_id)
# print("Perform Login:", perform_login)