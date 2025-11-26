"""Agent module for interacting with UAA and cloning repositories.

Refinements:
 - Environment-driven configuration for model and repo URL.
 - Retry logic for git clone with exponential backoff.
 - Logging configured only when executed as a script (not on import).
"""

# Standard library imports (alphabetized)
import logging
import os
import signal
import socket
import subprocess
import tempfile  # secure temporary directory creation
import threading
import time
import time as _time

# Third-party imports
from git import Repo
from google.adk.agents.llm_agent import Agent

# Local application imports
try:
    from .config import settings
except ImportError:
    from config import settings
try:
    from .uaa_server_information import UAAServerInformationClient
except ImportError:
    from uaa_server_information import UAAServerInformationClient

logger = logging.getLogger(__name__)

# Goals
# 1. Get UAA server version
# 2. Install UAA server
# 3. Build UAA server
# 4. Run UAA server
# 5. Update UAA server with appropriate human approvals
# 6. Constantly look for changes in the UAA repo and pull them in automatically (use GitHub tools)
# 7. Inform client about new updates to the UAA server


# root_agent initialization will occur after function definitions to ensure names are defined.


def get_uaa_version() -> str:
    """Get the current UAA server version (placeholder)."""
    return ''


def sdk_use_java_version(desired_version: str = "21.0.9-amzn") -> bool:
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
        if '21.0.9-amzn' in version_info:
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


def run_uaa_detached(destination_path: str, java_version: str = "21.0.9-amzn") -> dict:
    """
    Start UAA via Gradle in the background and detach.
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
            'source "$HOME/.sdkman/bin/sdkman-init.sh" && '
            'sdk env && '
            './gradlew run'
        )

        with open(stdout_log, "w") as stdout_file, open(stderr_log, "w") as stderr_file:
            proc = subprocess.Popen(
                ['bash', '-lc', shell_cmd],
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True  # Detach process group
            )

        logger.info("Started UAA (detached) with PID %d", proc.pid)

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


def clone_repository(
    repo_url: str,
    destination_path: str,
    max_retries: int = 3,
    attempt_timeout: float = 0.0,
) -> bool:
    """Clone a git repository with a simplified signature for agent tooling."""
    return _clone_repository_with_cancel(
        repo_url, destination_path, max_retries, attempt_timeout, cancel_event=None
    )


def _clone_repository_with_cancel(
    repo_url: str,
    destination_path: str,
    max_retries: int = 3,
    attempt_timeout: float = 0.0,
    cancel_event: threading.Event | None = None,
) -> bool:
    """Clone a git repository to a destination path with retry logic and optional timeout.

    Args:
        repo_url: HTTPS (or SSH) URL of the repository to clone.
        destination_path: Filesystem path where the repo should be cloned.
    max_retries: Number of retry attempts on failure (not counting initial attempt).
        attempt_timeout: Maximum seconds allowed for a single clone attempt. If exceeded, the attempt is considered failed and retried.

    Returns:
        True if clone succeeds, False otherwise.
    """

    def _attempt_clone() -> Exception | None:
        """Run Repo.clone_from inside a thread; return any exception raised."""
        captured: dict[str, Exception] = {}

        def _target():  # executed in worker thread
            try:
                Repo.clone_from(repo_url, destination_path)
            except Exception as exc:  # store exception to re-raise outside the thread
                captured['error'] = exc

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        # If no timeout specified, block until completion
        thread.join(timeout=attempt_timeout)
        if thread.is_alive():
            # Timed out; thread is still running. We cannot safely kill it; mark failure.
            logger.warning(
                "Clone attempt timed out after %.2f seconds for repo '%s'", attempt_timeout, repo_url
            )
            return TimeoutError(f"clone attempt exceeded timeout {attempt_timeout}s")
        # Completed; check for exception
        return captured.get('error')

    # Base backoff can be tuned via environment without increasing argument count.
    base_backoff = float(os.getenv('UAA_CLONE_BASE_BACKOFF', '1.0'))
    attempt = 0
    # Loop attempts: initial attempt + retries until success or exhaustion
    while attempt <= max_retries:
        if cancel_event and cancel_event.is_set():
            logger.info("Clone cancelled before attempt %d.", attempt)
            return False
        try:
            if attempt_timeout is None:
                Repo.clone_from(repo_url, destination_path)
                logger.info('Repository cloned successfully to %s', destination_path)
                return True
            else:
                error = _attempt_clone()
                if error is None:
                    logger.info('Repository cloned successfully to %s', destination_path)
                    return True
                else:
                    raise error
        except Exception as e:  # covers both Git failures and timeout wrapper raising
            attempt += 1
            if attempt > max_retries:
                logger.error(
                    "Failed cloning repository '%s' to '%s' after %d attempts: %s",
                    repo_url,
                    destination_path,
                    attempt - 1,
                    e,
                )
                return False
            sleep_for = base_backoff * (2 ** (attempt - 1))
            logger.warning(
                "Clone attempt %d for '%s' failed: %s. Retrying in %.2f seconds...",
                attempt,
                repo_url,
                e,
                sleep_for,
            )
            time.sleep(sleep_for)
    return False  # Defensive fallback


def ask_human_approval(prompt: str = "Do you approve this action? (y/n): ") -> bool:
    """Prompt the user for human approval and return True if approved, False otherwise."""
    while True:
        response = input(prompt).strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("Please enter 'y' or 'n'.")


# Now initialize root_agent after function definitions
uaa_server_information_client = UAAServerInformationClient(base_url=settings.uaa_base_url)
root_agent = Agent(
    model=settings.model,
    name='root_agent',
    description='Agent to manage users, user authentication and user authorization.',
    instruction='You are a helpful assistant that manages a UAA server and learns about users.',
    tools=[
        get_uaa_version,
        clone_repository,
        get_java_version,
        sdk_set_sdkmanrc_file,
        sdk_use_java_version,
        build_uaa,
        clean_uaa,
        run_uaa_detached,
        wait_for_port,
        stop_uaa,
        # ask_human_approval,
        uaa_server_information_client.get_server_information,
        uaa_server_information_client.get_openid_configuration,
        uaa_server_information_client.create_passcode,
        uaa_server_information_client.get_passcode,
        uaa_server_information_client.get_auto_login,
        uaa_server_information_client.create_auto_login,
        uaa_server_information_client.perform_login,
    ],
)

if __name__ == '__main__':
    # Configure logging only when running as a script to avoid overriding host application logging.
    logging.basicConfig(
        level=settings.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info('Logger initialized (script execution).')
    # Only run the example clone when invoked directly.
    # _example_clone()

# Examples

def _example_clone(repo_url: str | None = None) -> None:
    """Example: clone UAA repo into an ephemeral temporary directory under /tmp.

    The directory is cleaned up automatically when the context exits.
    Repo URL can be overridden via env UAA_REPO_URL.
    """
    repo_url = repo_url or os.getenv('UAA_REPO_URL', 'https://github.com/cloudfoundry/uaa')
    with tempfile.TemporaryDirectory(prefix='uaa_repo_', dir='/tmp') as tmpdir:
        logger.info("Cloning repository '%s' into temporary dir: %s", repo_url, tmpdir)
        success = clone_repository(repo_url, tmpdir)
        if success:
            try:
                logger.info('Clone completed. Contents: %s', os.listdir(tmpdir))
            except Exception:
                logger.debug('Could not list contents of %s', tmpdir)
        else:
            logger.warning('Clone failed; temporary directory will still be cleaned up.')