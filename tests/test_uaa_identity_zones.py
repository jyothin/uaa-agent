"""
Tests for the UAAIdentityZonesClient.
"""

import unittest
from unittest.mock import Mock, patch

import requests

from uaa_identity_zones import UAAIdentityZonesClient


class TestUAAIdentityZonesClient(unittest.TestCase):
    """
    Tests for the UAAIdentityZonesClient.
    """

    def setUp(self):
        """
        Set up the test client.
        """
        self.base_url = "http://localhost:8080/uaa"
        self.token = "test_token"
        self.client = UAAIdentityZonesClient(self.base_url, self.token)

    @patch('requests.post')
    def test_create_an_identity_zone_success(self, mock_post):
        """
        Test successful creation of an identity zone.
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        expected_response = {"id": "test_zone", "name": "Test Zone"}
        mock_response.json.return_value = expected_response
        mock_post.return_value = mock_response

        zone_id = "test_zone"
        subdomain = "test-zone"
        name = "Test Zone"
        description = "A test identity zone."

        # Act
        response = self.client.create_an_identity_zone(zone_id, subdomain, name, description)

        # Assert
        url = f"{self.base_url}/identity-zones"
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        payload = {
            "id": zone_id,
            "subdomain": subdomain,
            "name": name,
            "description": description,
        }
        mock_post.assert_called_once_with(url, headers=headers, json=payload)
        self.assertEqual(response, expected_response)

    @patch('requests.post')
    def test_create_an_identity_zone_http_error(self, mock_post):
        """
        Test HTTP error during identity zone creation.
        """
        # Arrange
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("409 Conflict")
        mock_post.return_value = mock_response

        zone_id = "existing_zone"
        subdomain = "existing-zone"
        name = "Existing Zone"
        description = "An existing identity zone."

        # Act & Assert
        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.create_an_identity_zone(zone_id, subdomain, name, description)

    @patch('requests.post')
    def test_create_an_identity_zone_connection_error(self, mock_post):
        """
        Test connection error during identity zone creation.
        """
        # Arrange
        mock_post.side_effect = requests.exceptions.ConnectionError

        zone_id = "test_zone"
        subdomain = "test-zone"
        name = "Test Zone"
        description = "A test identity zone."

        # Act
        result = self.client.create_an_identity_zone(zone_id, subdomain, name, description)

        # Assert
        self.assertEqual(result, {"error": "UAA server is not running."})


if __name__ == '__main__':
    unittest.main()
