from unittest.mock import MagicMock, patch

from uaa_server_information import UAAServerInformationClient

BASE_URL = "https://uaa.example.com"
TOKEN = "dummy-token"

@patch('uaa_server_information.requests.get')
def test_get_server_information(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"info": "server"})
    client = UAAServerInformationClient(BASE_URL, TOKEN)
    result = client.get_server_information()
    assert result == {"info": "server"}
    mock_get.assert_called_once()

@patch('uaa_server_information.requests.get')
def test_get_openid_configuration(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"openid": "config"})
    client = UAAServerInformationClient(BASE_URL, TOKEN)
    result = client.get_openid_configuration()
    assert result == {"openid": "config"}
    mock_get.assert_called_once()

@patch('uaa_server_information.requests.post')
def test_create_passcode(mock_post):
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"passcode": "created"})
    client = UAAServerInformationClient(BASE_URL, TOKEN)
    result = client.create_passcode()
    assert result == {"passcode": "created"}
    mock_post.assert_called_once()

@patch('uaa_server_information.requests.get')
def test_get_passcode(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"passcode": "current"})
    client = UAAServerInformationClient(BASE_URL, TOKEN)
    result = client.get_passcode()
    assert result == {"passcode": "current"}
    mock_get.assert_called_once()

@patch('uaa_server_information.requests.get')
def test_get_auto_login(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"auto_login": "info"})
    client = UAAServerInformationClient(BASE_URL, TOKEN)
    result = client.get_auto_login()
    assert result == {"auto_login": "info"}
    mock_get.assert_called_once()

@patch('uaa_server_information.requests.post')
def test_create_auto_login(mock_post):
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"auto_login": "created"})
    client = UAAServerInformationClient(BASE_URL, TOKEN)
    result = client.create_auto_login("user", "pass")
    assert result == {"auto_login": "created"}
    mock_post.assert_called_once()

@patch('uaa_server_information.requests.get')
def test_perform_login(mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"login": "performed"})
    client = UAAServerInformationClient(BASE_URL, TOKEN)
    result = client.perform_login("code123", "clientid123")
    assert result == {"login": "performed"}
    mock_get.assert_called_once()
