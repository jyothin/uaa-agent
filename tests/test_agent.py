import os
from unittest.mock import patch

# Import the module under test
import agent

@patch('agent.Repo')
def test_clone_repository_success(mock_repo):
    mock_repo.clone_from.return_value = None  # Successful clone
    tmpdir = '/tmp/test_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        assert agent.clone_repository('https://example.com/repo.git', tmpdir) is True
        mock_repo.clone_from.assert_called_once_with('https://example.com/repo.git', tmpdir)
    finally:
        # Cleanup created directory
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)

@patch('agent.Repo')
def test_clone_repository_retries_and_fails(mock_repo):
    mock_repo.clone_from.side_effect = Exception('network error')
    tmpdir = '/tmp/test_fail'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        assert agent.clone_repository('https://example.com/repo.git', tmpdir, max_retries=2, retry_backoff=0.01) is False
        # Should be called 3 times: initial attempt + 2 retries
        EXPECTED_ATTEMPTS = 3
        assert mock_repo.clone_from.call_count == EXPECTED_ATTEMPTS
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


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
