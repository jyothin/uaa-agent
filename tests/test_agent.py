from unittest.mock import patch

# Import the modules under test
import agent
from uaa_identity_zones import UAAIdentityZonesClient

ONE = 1
TWO = 2


def test_example_clone_env_override(monkeypatch):
    # Ensure environment override works
    monkeypatch.setenv('UAA_REPO_URL', 'https://example.com/env-repo.git')
    # Patch clone_repository to avoid real clone
    with patch('agent.clone_repository', return_value=True) as mock_clone:
        agent._example_clone()
        # Validate it used env override
        mock_clone.assert_called()
        called_url = mock_clone.call_args[0][0]
        assert called_url == 'https://example.com/env-repo.git'


def test_set_token_for_uaa_identity_zones_client():
    """
    Test that the token for the UAAIdentityZonesClient can be set correctly.
    """
    # Given
    original_token = UAAIdentityZonesClient.token
    new_token = "new-test-token"
    assert original_token != new_token

    # When
    agent.set_token_for_uaa_identity_zones_client(new_token)

    # Then
    assert UAAIdentityZonesClient.token == new_token

    # Reset token to original value to avoid side effects in other tests
    UAAIdentityZonesClient.token = original_token
