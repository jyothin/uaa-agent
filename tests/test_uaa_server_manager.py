import os
from unittest.mock import MagicMock, mock_open, patch

# Import the modules under test
import agent
import uaa_server_manager

TEST_PID = 12345


@patch('uaa_server_manager.subprocess.run')
def test_build_uaa_success(mock_run):
    # Simulate successful build
    mock_run.return_value = MagicMock(stdout='Success', returncode=0)
    tmpdir = '/tmp/test_build_uaa_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        # Should succeed if directory exists and subprocess.run returns success
        result = uaa_server_manager.build_uaa(tmpdir)
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


@patch('uaa_server_manager.subprocess.run')
def test_build_uaa_failure(mock_run):
    # Simulate build failure
    mock_run.side_effect = Exception('Build failed')
    tmpdir = '/tmp/test_build_uaa_failure'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = uaa_server_manager.build_uaa(tmpdir)
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



@patch('uaa_server_manager.subprocess.run')
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
    result = uaa_server_manager.build_uaa(tmpdir)
    assert result is False


@patch('uaa_server_manager.subprocess.Popen')
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


@patch('uaa_server_manager.subprocess.Popen')
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


@patch('uaa_server_manager.subprocess.Popen')
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


@patch('uaa_server_manager.subprocess.run')
def test_get_java_version_success(mock_run):
    # Simulate successful run
    mock_run.return_value = MagicMock(stderr='openjdk version "21.0.9-amzn" 2024-10-15\nOther lines', returncode=0)
    result = agent.get_java_version()
    assert 'openjdk version "21.0.9-amzn"' in result
    mock_run.assert_called_once_with(['java', '-version'], capture_output=True, text=True, check=True)


@patch('uaa_server_manager.subprocess.run')
def test_get_java_version_not_found(mock_run):
    # Simulate FileNotFoundError
    mock_run.side_effect = FileNotFoundError
    result = agent.get_java_version()
    assert result == "Java not found"


@patch('uaa_server_manager.subprocess.run')
def test_get_java_version_command_error(mock_run):
    # Simulate CalledProcessError
    mock_run.side_effect = uaa_server_manager.subprocess.CalledProcessError(1, ['java', '-version'])
    result = agent.get_java_version()
    assert result == "Error checking Java version"


@patch('uaa_server_manager.subprocess.run')
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


@patch('uaa_server_manager.subprocess.run')
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


@patch('uaa_server_manager.subprocess.run')
def test_get_java_version_from_sdkmanrc_command_error(mock_run):
    # Simulate CalledProcessError
    mock_run.side_effect = uaa_server_manager.subprocess.CalledProcessError(1, ['cat', '.sdkmanrc'])
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


@patch('uaa_server_manager.subprocess.run')
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


@patch('uaa_server_manager.subprocess.run')
def test_assemble_uaa_success(mock_run):
    # Simulate successful assemble
    mock_run.return_value = MagicMock(stdout='Success', returncode=0)
    tmpdir = '/tmp/test_assemble_uaa_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        # Should succeed if directory exists and subprocess.run returns success
        result = agent.assemble_uaa(tmpdir)
        assert result is True
        mock_run.assert_called_once_with(['bash', '-lc', 'source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk env && ./gradlew assemble'], check=True, capture_output=True, text=True, timeout=600)
    finally:
        # Cleanup
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('uaa_server_manager.subprocess.run')
def test_assemble_uaa_failure(mock_run):
    # Simulate assemble failure
    mock_run.side_effect = Exception('Assemble failed')
    tmpdir = '/tmp/test_assemble_uaa_failure'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.assemble_uaa(tmpdir)
        assert result is False
        mock_run.assert_called_once_with([
            'bash', '-lc', 'source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk env && ./gradlew assemble'
        ], check=True, capture_output=True, text=True, timeout=600)
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('uaa_server_manager.subprocess.run')
def test_assemble_uaa_no_directory(mock_run):
    # Directory does not exist
    tmpdir = '/tmp/nonexistent_assemble_uaa_dir'
    if os.path.isdir(tmpdir):
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(tmpdir)
    result = agent.assemble_uaa(tmpdir)
    assert result is False


def test_check_certificates_exist_success():
    # Create a temporary directory and the required certificate file
    tmpdir = '/tmp/test_check_certificates_exist_success'
    cert_path = os.path.join(tmpdir, "scripts/certificates")
    os.makedirs(cert_path, exist_ok=True)
    cert_file = os.path.join(cert_path, "uaa_keystore.p12")
    with open(cert_file, 'w') as f:
        f.write('dummy cert')
    
    try:
        result = agent.check_certificates_exist(tmpdir)
        assert result is True
    finally:
        # Cleanup
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


def test_check_certificates_exist_failure():
    # Create a temporary directory without the certificate file
    tmpdir = '/tmp/test_check_certificates_exist_failure'
    os.makedirs(tmpdir, exist_ok=True)
    
    try:
        result = agent.check_certificates_exist(tmpdir)
        assert result is False
    finally:
        # Cleanup
        if os.path.isdir(tmpdir):
            os.rmdir(tmpdir)


@patch('uaa_server_manager.subprocess.Popen')
@patch('builtins.open', new_callable=mock_open)
def test_generate_certificate_success(mock_file_open, mock_popen):
    # Simulate successful Popen
    mock_proc = MagicMock()
    mock_proc.pid = TEST_PID
    mock_popen.return_value = mock_proc

    tmpdir = '/tmp/test_generate_certificate_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.generate_certificate(tmpdir)
        assert result['success'] is True
        assert result['pid'] == TEST_PID
        
        shell_cmd = (
            f'{tmpdir}/scripts/certificates/generate.sh'
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


@patch('uaa_server_manager.subprocess.Popen')
def test_generate_certificate_failure(mock_popen):
    # Simulate Popen failure
    mock_popen.side_effect = Exception('Popen failed')
    tmpdir = '/tmp/test_generate_certificate_failure'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        result = agent.generate_certificate(tmpdir)
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


def test_generate_certificate_no_directory():
    # Directory does not exist
    tmpdir = '/tmp/nonexistent_cert_dir'
    if os.path.isdir(tmpdir):
        os.rmdir(tmpdir)
    result = agent.generate_certificate(tmpdir)
    assert result['success'] is False
    assert result['error'] == 'invalid path'
