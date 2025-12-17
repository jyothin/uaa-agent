"""UAA Server manager and local runtime utilities.

Provides tools for:
- Java/SDKMAN helpers: `sdk_use_java_version`, `sdk_set_sdkmanrc_file`,
  `get_java_version`, `get_java_version_from_sdkmanrc`
- Build/assemble: `build_uaa`, `assemble_uaa`
- Run/stop/network: `run_uaa_detached`, `wait_for_port`, `stop_uaa`
- Certificates: `check_certificates_exist`, `generate_certificate`
- Cleanup: `clean_uaa`

These functions are orchestrated by `agent.py` to manage a local UAA checkout
via Gradle and SDKMAN.
"""

import logging
import os
import signal
import socket
import subprocess
import threading
import time
import time as _time

try:
    from .config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


def sdk_use_java_version(desired_version: str = settings.uaa_java_version) -> bool:
    """Attempt to switch the active Java version using SDKMAN.

    This runs `sdk use java <desired_version>` inside a login shell so that SDKMAN's environment is loaded.

    Args:
        desired_version: The Java version identifier managed by SDKMAN.
    Returns:
        True if the command executed successfully, False otherwise.
    """
    sdk_cmd = f"sdk use java {desired_version}"
    sdk_result = subprocess.run(['bash', '-lc', sdk_cmd], check=False, capture_output=True, text=True)
    if sdk_result.returncode == 0:
        logger.info("Switched Java version using SDKMAN: %s", desired_version)
        return True
    logger.debug(
        "Failed to switch Java version to %s (exit %s). stderr: %s",
        desired_version,
        sdk_result.returncode,
        sdk_result.stderr.strip(),
    )
    return False


def sdk_set_sdkmanrc_file(desired_version: str,
                          destination_path: str) -> bool:
    """Create or update the .sdkmanrc file to specify the desired Java version.

    Args:
        desired_version: The Java version identifier managed by SDKMAN.
        destination_path: The path where the .sdkmanrc file should be created.
    Returns:
        True if the .sdkmanrc file was created or updated successfully, False otherwise.
    """
    try:
        if not os.path.isdir(destination_path):
            logger.error("Destination path does not exist or is not a directory: %s", destination_path)
            return False
        logger.info("Changing to destination path: %s", destination_path)
        os.chdir(destination_path)

        with open('.sdkmanrc', 'w', encoding="utf-8") as sdkmanrc:
            sdkmanrc.write(f"java={desired_version}\n")
        logger.info(".sdkmanrc file created/updated with Java version: %s", desired_version)
        return True
    except Exception as e:
        logger.error("Failed to create/update .sdkmanrc file: %s", e)
        return False


def get_java_version() -> str:
    """Return the installed Java version string (first line of `java -version`).

    Performs a semantic check for Amazon Corretto 21.0.9 and logs accordingly.
    Returns an error string if Java is missing or the command fails.
    """
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True, check=True)
        version_info = result.stderr.splitlines()[0]
        if settings.uaa_java_version in version_info:
            logger.info("Detected Amazon Corretto JDK 21.0.9.")
        else:
            logger.debug("Java version is not Amazon Corretto 21.0.9: %s", version_info)
        logger.info("Java version found: %s", version_info)
        return version_info
    except FileNotFoundError:
        logger.error("Java is not installed or not found in PATH.")
        return "Java not found"
    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while checking Java version: %s", e)
        return "Error checking Java version"


def get_java_version_from_sdkmanrc(destination_path: str) -> str:
    """Return the Java version string from the sdkrmanrc file in the destination path.

    Returns an error string if Java is missing or the command fails.
    """
    try:
        if not os.path.isdir(destination_path):
            logger.error("Destination path does not exist or is not a directory: %s", destination_path)
            return "Destination path does not exist or is not a directory"
        logger.info("Changing to destination path: %s", destination_path)
        os.chdir(destination_path)

        result = subprocess.run(['cat', f'{destination_path}/.sdkmanrc'], capture_output=True, text=True, check=True)
        version_info = result.stdout.splitlines()[0].split('=')[1]
        if settings.uaa_java_version in version_info:
            logger.info("Detected Amazon Corretto JDK 21.0.9 in .sdkmanrc.")
        else:
            logger.debug("Java version is not Amazon Corretto 21.0.9: %s", version_info)
        logger.info("Java version found: %s", version_info)
        return version_info
    except FileNotFoundError:
        logger.error("Java is not installed or not found in PATH.")
        return "Java not found"
    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while checking Java version: %s", e)
        return "Error checking Java version"


def wait_for_port(host: str = '127.0.0.1', port: int = 8080, timeout: int = 30, interval: float = 1.0) -> bool:
    """Probe a TCP host:port until it becomes reachable or timeout expires.

    Args:
        host: Hostname or IP to probe.
        port: TCP port to check.
        timeout: Total seconds to wait before giving up.
        interval: Seconds to sleep between attempts.
    Returns:
        True if the port is reachable within timeout, otherwise False.
    """
    deadline = _time.time() + timeout
    attempt = 0
    while _time.time() < deadline:
        attempt += 1
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(interval)
            if sock.connect_ex((host, port)) == 0:
                logger.info("Port %d on %s is reachable after %d attempt(s).", port, host, attempt)
                return True
        logger.debug("Port %d on %s not open yet (attempt %d).", port, host, attempt)
        _time.sleep(interval)
    logger.warning("Port %d on %s not reachable within %ds.", port, host, timeout)
    return False


def stop_uaa(pid: int, grace_seconds: int = 10) -> bool:
    """Gracefully stop a detached UAA process identified by its PID.

    Sends SIGTERM to the process group first (assuming it was started with a new session),
    waits up to grace_seconds for it to exit, then sends SIGKILL if still alive.

    Args:
        pid: PID of the originally launched UAA process (also the process group id).
        grace_seconds: Seconds to wait after SIGTERM before forcing termination.
    Returns:
        True if the process was terminated (graceful or forced); False if not found or error.
    """
    try:
        os.killpg(pid, signal.SIGTERM)
        logger.info("Sent SIGTERM to UAA process group %d", pid)
    except ProcessLookupError:
        logger.warning("Process group %d not found (already stopped).", pid)
        return False
    except Exception as e:
        logger.error("Failed sending SIGTERM to %d: %s", pid, e)
        return False

    end = time.time() + grace_seconds
    while time.time() < end:
        try:
            os.kill(pid, 0)  # Check existence
        except ProcessLookupError:
            logger.info("UAA process group %d stopped gracefully.", pid)
            return True
        time.sleep(0.5)

    try:
        os.killpg(pid, signal.SIGKILL)
        logger.warning("Forced SIGKILL sent to UAA process group %d after %ds grace.", pid, grace_seconds)
        return True
    except ProcessLookupError:
        logger.info("Process group %d already gone during SIGKILL attempt.", pid)
        return True
    except Exception as e:
        logger.error("Failed sending SIGKILL to %d: %s", pid, e)
        return False


def build_uaa(destination_path: str) -> bool:
    """Build the UAA server at the given filesystem path.
       Before building, ensure that the .sdkmanrc file is set to the desired Java version using the tool get_java_version_from_sdkmanrc.

    Args:
        destination_path: Path to the cloned UAA repository root.
    Returns:
        True if the Gradle build succeeds, otherwise False.
    """
    try:
        if not os.path.isdir(destination_path):
            logger.error("Destination path does not exist or is not a directory: %s", destination_path)
            return False
        logger.info("Changing to destination path: %s", destination_path)
        os.chdir(destination_path)

        result: dict[str, object] = {}

        def _run_build() -> None:
            try:
                # Use .sdkmanrc to set Java version, activate SDKMAN env, then build with Gradle.
                shell_cmd = (
                    'source "$HOME/.sdkman/bin/sdkman-init.sh" && '
                    'sdk env && '
                    './gradlew build'
                )
                proc = subprocess.run(
                    ['bash', '-lc', shell_cmd],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=600  # Optional: prevent hanging builds (adjust as needed)
                )
                result['stdout'] = proc.stdout
                result['stderr'] = proc.stderr
                result['success'] = proc.returncode == 0
            except Exception as exc:  # capture any failure
                result['error'] = exc
                result['success'] = False

        logger.info("Starting build in background thread...\n")
        thread = threading.Thread(target=_run_build, daemon=False)
        thread.start()
        thread.join()  # Wait until build completes (can be extended with timeout if needed)

        if result.get('success'):
            stderr = result.get('stderr')
            if stderr:
                logger.debug("Build stderr:\n%s", stderr)
            return True
        else:
            error = result.get('error')
            if error:
                logger.error("Gradle build failed: %s", error)
            return False
    except Exception as e:
        logger.error("Build or run failed: %s", e)
        return False

        # Ensure gradlew exists
        gradlew = os.path.join(destination_path, "gradlew")
        if not (os.path.isfile(gradlew) and os.access(gradlew, os.X_OK)):
            logger.error("gradlew not found or not executable at %s", gradlew)
            return {"success": False, "error": "gradlew missing"}


def assemble_uaa(destination_path: str) -> bool:
    """Assemble the UAA server at the given filesystem path.
       Before assembling, ensure that the .sdkmanrc file is set to the desired Java version using the tool get_java_version_from_sdkmanrc.

    Args:
        destination_path: Path to the cloned UAA repository root.
    Returns:
        True if the Gradle assemble succeeds, otherwise False.
    """
    try:
        if not os.path.isdir(destination_path):
            logger.error("Destination path does not exist or is not a directory: %s", destination_path)
            return False
        logger.info("Changing to destination path: %s", destination_path)
        os.chdir(destination_path)

        result: dict[str, object] = {}

        def _run_assemble() -> None:
            try:
                # Use .sdkmanrc to set Java version, activate SDKMAN env, then build with Gradle.
                shell_cmd = (
                    'source "$HOME/.sdkman/bin/sdkman-init.sh" && '
                    'sdk env && '
                    './gradlew assemble'
                )
                proc = subprocess.run(
                    ['bash', '-lc', shell_cmd],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=600  # Optional: prevent hanging assembles (adjust as needed)
                )
                result['stdout'] = proc.stdout
                result['stderr'] = proc.stderr
                result['success'] = proc.returncode == 0
            except Exception as exc:  # capture any failure
                result['error'] = exc
                result['success'] = False

        logger.info("Starting assemble in background thread...\n")
        thread = threading.Thread(target=_run_assemble, daemon=False)
        thread.start()
        thread.join()  # Wait until assemble completes (can be extended with timeout if needed)

        if result.get('success'):
            stderr = result.get('stderr')
            if stderr:
                logger.debug("Build stderr:\n%s", stderr)
            return True
        else:
            error = result.get('error')
            if error:
                logger.error("Gradle build failed: %s", error)
            return False
    except Exception as e:
        logger.error("Assemble or run failed: %s", e)
        return False


def clean_uaa(destination_path: str) -> bool:
    """Clean the UAA server build artifacts by running `./gradlew clean`.

    Args:
        destination_path: Path to the cloned UAA repository root.
    Returns:
        True if the Gradle clean command succeeds, otherwise False.
    """
    try:
        if not os.path.isdir(destination_path):
            logger.error("Destination path does not exist or is not a directory: %s", destination_path)
            return False
        os.chdir(destination_path)

        shell_cmd = (
            'source "$HOME/.sdkman/bin/sdkman-init.sh" && '
            'sdk env && '
            './gradlew clean'
        )
        result_run = subprocess.run(
            ['bash', '-lc', shell_cmd],
            check=True,
            capture_output=True,
            text=True,
            timeout=600
        )
        logger.info("Run output:\n%s", result_run.stdout)
        stderr = result_run.stderr
        if stderr:
            logger.debug("Run stderr:\n%s", stderr)
        return result_run.returncode == 0
    except Exception as e:
        logger.error("Clean command failed: %s", e)
        return False


def check_certificates_exist(destination_path: str) -> bool:
    """Check if the required UAA certificates exist in the specified path.

    Args:
        destination_path: Path to the cloned UAA repository root.
    Returns:
        True if all required certificate files exist, otherwise False.
    """
    required_files = [
        os.path.join(destination_path, "scripts/certificates", "uaa_keystore.p12"),
    ]

    for file_path in required_files:
        if not os.path.isfile(file_path):
            logger.warning("Required certificate file not found: %s", file_path)
            return False
    logger.info("All required certificate files are present.")
    return True


def generate_certificate(destination_path: str) -> dict:
    """
    Generate certificates in the background and detach.
    Returns dict with pid, stdout_log, stderr_log, success flag (launch only).
    """
    try:
        if not os.path.isdir(destination_path):
            logger.error("Destination path invalid: %s", destination_path)
            return {"success": False, "error": "invalid path"}
        os.chdir(destination_path)

        stdout_log = os.path.join(destination_path, "uaa_run.out")
        stderr_log = os.path.join(destination_path, "uaa_run.err")

        shell_cmd = (
            f'{destination_path}/scripts/certificates/generate.sh'
        )

        with open(stdout_log, "w") as stdout_file, open(stderr_log, "w") as stderr_file:
            proc = subprocess.Popen(
                ['bash', '-lc', shell_cmd],
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True  # Detach process group
            )

        logger.info("Generated certificates with PID %d", proc.pid)

        # Save the PID to a file in the workspace root
        try:
            # Assuming the script is run from the workspace root, or settings.root_dir is available
            pid_file_path = 'proc.pid'
            with open(pid_file_path, "w") as pid_file:
                pid_file.write(str(proc.pid))
            logger.info("Saved certificates PID %d to %s", proc.pid, pid_file_path)
        except Exception as e:
            logger.error("Failed to save PID to file: %s", e)

        return {
            "success": True,
            "pid": proc.pid,
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
        }
    except Exception as e:
        logger.error("Failed to generate certificates detached: %s", e)
        return {"success": False, "error": str(e)}


def run_uaa_detached(destination_path: str, java_version: str = settings.uaa_java_version) -> dict:
    """
    Start UAA via Gradle in the background and detach.
    Returns dict with pid, stdout_log, stderr_log, success flag (launch only).
    Before running, ensure that the client_secret for the 'admin' client ID is updated in uaa.yaml.
    """
    try:
        if not os.path.isdir(destination_path):
            logger.error("Destination path invalid: %s", destination_path)
            return {"success": False, "error": "invalid path"}
        os.chdir(destination_path)

        stdout_log = os.path.join(destination_path, "uaa_run.out")
        stderr_log = os.path.join(destination_path, "uaa_run.err")

        shell_cmd = (
            'source "$HOME/.sdkman/bin/sdkman-init.sh" && '
            'sdk env && '
            f'{destination_path}/scripts/boot/boot-with-tls.sh'
            # f'CLOUDFOUNDRY_CONFIG_PATH={destination_path}/scripts/boot ./gradlew run'
        )

        with open(stdout_log, "w") as stdout_file, open(stderr_log, "w") as stderr_file:
            proc = subprocess.Popen(
                ['bash', '-lc', shell_cmd],
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True  # Detach process group
            )

        logger.info("Started UAA (detached) with PID %d", proc.pid)

        # Save the PID to a file in the workspace root
        try:
            # Assuming the script is run from the workspace root, or settings.root_dir is available
            pid_file_path = 'proc.pid'
            with open(pid_file_path, "w") as pid_file:
                pid_file.write(str(proc.pid))
            logger.info("Saved UAA PID %d to %s", proc.pid, pid_file_path)
        except Exception as e:
            logger.error("Failed to save PID to file: %s", e)

        return {
            "success": True,
            "pid": proc.pid,
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
            "java_version": java_version
        }
    except Exception as e:
        logger.error("Failed to launch UAA detached: %s", e)
        return {"success": False, "error": str(e)}
