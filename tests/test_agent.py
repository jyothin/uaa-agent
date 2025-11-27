import os
import time
from unittest.mock import MagicMock, patch, mock_open

# Import the module under test
import agent

ONE = 1
TWO = 2
THREE = 3
TEST_PID = 12345

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
        # Use env var to minimize backoff duration for test speed
        os.environ['UAA_CLONE_BASE_BACKOFF'] = '0.01'
        assert agent.clone_repository('https://example.com/repo.git', tmpdir, max_retries=2) is False
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


@patch('agent.Repo')
def test_clone_repository_timeout_retries(mock_repo):
    # Simulate a slow clone function exceeding attempt_timeout
    def slow_clone(*args, **kwargs):
        time.sleep(0.05)  # longer than our attempt_timeout below

    mock_repo.clone_from.side_effect = slow_clone
    tmpdir = '/tmp/test_timeout'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        os.environ['UAA_CLONE_BASE_BACKOFF'] = '0.001'
        result = agent.clone_repository(
            'https://example.com/slow.git', tmpdir, max_retries=2, attempt_timeout=0.01
        )
        # Should fail after exhausting retries due to timeout each attempt
        assert result is False
        # initial + 2 retries = 3 attempts
        assert mock_repo.clone_from.call_count == THREE
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


# TODO: Re-enable when cancellation handling is implemented
# @patch('agent.Repo')
# def test_clone_repository_cancelled_before_start(mock_repo):
#     cancel = Event()
#     cancel.set()  # cancellation signaled before first attempt
#     tmpdir = '/tmp/test_cancel'
#     os.makedirs(tmpdir, exist_ok=True)
#     try:
#         result = agent.clone_repository(
#             'https://example.com/repo.git', tmpdir, cancel_event=cancel, max_retries=THREE
#         )
#         assert result is False
#         mock_repo.clone_from.assert_not_called()
#     finally:
#         if os.path.isdir(tmpdir):
#             for root, dirs, files in os.walk(tmpdir, topdown=False):
#                 for f in files:
#                     os.remove(os.path.join(root, f))
#                 for d in dirs:
#                     os.rmdir(os.path.join(root, d))
#             os.rmdir(tmpdir)


@patch('agent.subprocess.run')
def test_build_uaa_success(mock_run):
    # Simulate successful build
    mock_run.return_value = MagicMock(stdout='Success', returncode=0)
    tmpdir = '/tmp/test_build_uaa_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        # Should succeed if directory exists and subprocess.run returns success
        result = agent.build_uaa(tmpdir)
        assert result is True
        mock_run.assert_called_once_with(['bash', '-lc', 'source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk env && ./gradlew build'], check=True, capture_output=True, text=True, timeout=600)
    finally:
        # Cleanup
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('agent.subprocess.run')
def test_build_uaa_failure(mock_run):
    # Simulate build failure
    mock_run.side_effect = Exception('Build failed')
    tmpdir = '/tmp/test_build_uaa_failure'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.build_uaa(tmpdir)
        assert result is False
        mock_run.assert_called_once_with([
            'bash', '-lc', 'source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk env && ./gradlew build'
        ], check=True, capture_output=True, text=True, timeout=600)
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)



@patch('agent.subprocess.run')
def test_build_uaa_no_directory(mock_run):
    # Directory does not exist
    tmpdir = '/tmp/nonexistent_build_uaa_dir'
    if os.path.isdir(tmpdir):
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(tmpdir)
    result = agent.build_uaa(tmpdir)
    assert result is False


@patch('agent.subprocess.Popen')
@patch('builtins.open', new_callable=mock_open)
def test_run_uaa_success(mock_file_open, mock_popen):
    # Simulate successful Popen
    mock_proc = MagicMock()
    mock_proc.pid = 12345
    mock_popen.return_value = mock_proc

    tmpdir = '/tmp/test_run_uaa_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.run_uaa_detached(tmpdir)
        assert result['success'] is True
        assert result['pid'] == TEST_PID
        
        shell_cmd = (
            'source "$HOME/.sdkman/bin/sdkman-init.sh" && '
            'sdk env && '
            f'{tmpdir}/scripts/boot/boot-with-tls.sh'
        )
        
        # Get the arguments from the mock call
        call_args, call_kwargs = mock_popen.call_args
        
        # Check the command
        assert call_args[0] == ['bash', '-lc', shell_cmd]
        
        # Check other parameters
        assert 'start_new_session' in call_kwargs and call_kwargs['start_new_session'] is True
        assert 'stdout' in call_kwargs
        assert 'stderr' in call_kwargs

        # Check that the PID file was written
        mock_file_open.assert_any_call('proc.pid', 'w')
        mock_file_open().write.assert_called_once_with(str(TEST_PID))

    finally:
        if os.path.isdir(tmpdir):
            # Clean up the directory
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(tmpdir)


@patch('agent.subprocess.Popen')
def test_run_uaa_failure(mock_popen):
    # Simulate Popen failure
    mock_popen.side_effect = Exception('Popen failed')
    tmpdir = '/tmp/test_run_uaa_failure'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.run_uaa_detached(tmpdir)
        assert result['success'] is False
        assert 'error' in result
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('agent.subprocess.Popen')
def test_run_uaa_no_directory(mock_popen):
    # Simulate Popen raising FileNotFoundError for missing directory
    mock_popen.side_effect = FileNotFoundError('No such file or directory')
    tmpdir = '/tmp/nonexistent_run_uaa_dir'
    if os.path.isdir(tmpdir):
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(tmpdir)
    result = agent.run_uaa_detached(tmpdir)
    assert result['success'] is False


@patch('agent.subprocess.run')
def test_get_java_version_success(mock_run):
    # Simulate successful run
    mock_run.return_value = MagicMock(stderr='openjdk version "21.0.9-amzn" 2024-10-15\nOther lines', returncode=0)
    result = agent.get_java_version()
    assert 'openjdk version "21.0.9-amzn"' in result
    mock_run.assert_called_once_with(['java', '-version'], capture_output=True, text=True, check=True)


@patch('agent.subprocess.run')
def test_get_java_version_not_found(mock_run):
    # Simulate FileNotFoundError
    mock_run.side_effect = FileNotFoundError
    result = agent.get_java_version()
    assert result == "Java not found"


@patch('agent.subprocess.run')
def test_get_java_version_command_error(mock_run):
    # Simulate CalledProcessError
    mock_run.side_effect = agent.subprocess.CalledProcessError(1, ['java', '-version'])
    result = agent.get_java_version()
    assert result == "Error checking Java version"


@patch('agent.subprocess.run')
def test_get_java_version_from_sdkmanrc_success(mock_run):
    # Simulate successful run
    mock_run.return_value = MagicMock(stdout='java=21.0.9-amzn\n', returncode=0)
    tmpdir = '/tmp/test_get_java_version_from_sdkmanrc_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.get_java_version_from_sdkmanrc(tmpdir)
        assert '21.0.9-amzn' in result
        mock_run.assert_called_once_with(['cat', f'{tmpdir}/.sdkmanrc'], capture_output=True, text=True, check=True)
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('agent.subprocess.run')
def test_get_java_version_from_sdkmanrc_not_found(mock_run):
    # Simulate FileNotFoundError
    mock_run.side_effect = FileNotFoundError
    tmpdir = '/tmp/test_get_java_version_from_sdkmanrc_not_found'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.get_java_version_from_sdkmanrc(tmpdir)
        assert result == "Java not found"
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('agent.subprocess.run')
def test_get_java_version_from_sdkmanrc_command_error(mock_run):
    # Simulate CalledProcessError
    mock_run.side_effect = agent.subprocess.CalledProcessError(1, ['cat', '.sdkmanrc'])
    tmpdir = '/tmp/test_get_java_version_from_sdkmanrc_command_error'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.get_java_version_from_sdkmanrc(tmpdir)
        assert result == "Error checking Java version"
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('agent.subprocess.run')
def test_get_java_version_from_sdkmanrc_no_directory(mock_run):
    # Directory does not exist
    tmpdir = '/tmp/nonexistent_sdkmanrc_dir'
    if os.path.isdir(tmpdir):
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(tmpdir)
    result = agent.get_java_version_from_sdkmanrc(tmpdir)
    assert result == "Destination path does not exist or is not a directory"
