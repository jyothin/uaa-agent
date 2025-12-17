"""
Tests for the UAAClientCredentialsGrantClient.
"""

import unittest
from unittest.mock import Mock, patch

import requests

from uaa_token import UAAClientCredentialsGrantClient


class TestUAAClientCredentialsGrantClient(unittest.TestCase):
    """
    Tests for the UAAClientCredentialsGrantClient.
    """

    def setUp(self):
        """
        Set up the test client.
        """
        self.base_url = "http://localhost:8080/uaa"
        self.client = UAAClientCredentialsGrantClient(self.base_url)

    @patch('requests.post')
    def test_create_without_authorization_success(self, mock_post):
        """
        Test successful token retrieval without authorization.
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        expected_token = {"access_token": "test_token", "token_type": "bearer"}
        mock_response.json.return_value = expected_token
        mock_post.return_value = mock_response

        client_id = "test_client"
        client_secret = "test_secret"
        token_format = "jwt"
        scope = ["uaa.resource", "openid"]

        # Act
        token = self.client.create_without_authorization(client_id, client_secret, token_format, scope)

        # Assert
        url = f"{self.base_url}/oauth/token"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'token_format': token_format,
            'scope': ' '.join(scope)
        }
        mock_post.assert_called_once_with(url, headers=headers, data=data)
        self.assertEqual(token, expected_token)

    @patch('requests.post')
    def test_create_without_authorization_http_error(self, mock_post):
        """
        Test HTTP error during token retrieval.
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 401
        http_error = requests.exceptions.HTTPError("401 Unauthorized", response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        client_id = "test_client"
        client_secret = "wrong_secret"

        # Act & Assert
        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.create_without_authorization(client_id, client_secret, "", [])

    @patch('requests.post')
    def test_create_without_authorization_connection_error(self, mock_post):
        """
        Test connection error during token retrieval.
        """
        # Arrange
        mock_post.side_effect = requests.exceptions.ConnectionError

        client_id = "test_client"
        client_secret = "test_secret"

        # Act
        result = self.client.create_without_authorization(client_id, client_secret, "", [])

        # Assert
        self.assertEqual(result, {"error": "UAA server is not running."})

    @patch('requests.post')
    def test_create_without_authorization_bad_request(self, mock_post):
        """
        Test bad request error during token retrieval.
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 400
        http_error = requests.exceptions.HTTPError("400 Bad Request", response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        client_id = "invalid_client"
        client_secret = "test_secret"

        # Act
        result = self.client.create_without_authorization(client_id, client_secret, "", [])

        # Assert
        self.assertEqual(result, {"error": "Bad Request: The UAA server could not process the token request. "
                                         "Please check the client ID, secret, and grant type."})


if __name__ == '__main__':
    unittest.main()
