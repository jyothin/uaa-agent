"""Agent module for interacting with UAA and cloning repositories.

Refinements:
 - Environment-driven configuration for model and repo URL.
 - Retry logic for git clone with exponential backoff.
 - Logging configured only when executed as a script (not on import).
"""

# Standard library imports (alphabetized)
import logging
import os
import tempfile  # secure temporary directory creation
import threading
import time

# Third-party imports
from git import Repo
from google.adk.agents.llm_agent import Agent

# Local application imports
from config import settings

logger = logging.getLogger(__name__)

# Goals
# 1. Get UAA server version
# 2. Install UAA server


# root_agent initialization will occur after function definitions to ensure names are defined.


def get_uaa_version() -> str:
    """Get the current UAA server version"""
    return ''


def install_uaa(repo_url, destination_path) -> bool:
    """Install UAA server"""
    status = clone_repository(repo_url, destination_path)
    return status


def clone_repository(
    repo_url: str,
    destination_path: str,
    max_retries: int = 3,
    attempt_timeout: float | None = None,
    cancel_event: threading.Event | None = None,
) -> bool:
    """Clone a git repository to a destination path with retry logic and optional timeout.

    Args:
        repo_url: HTTPS (or SSH) URL of the repository to clone.
        destination_path: Filesystem path where the repo should be cloned.
    max_retries: Number of retry attempts on failure (not counting initial attempt).
        attempt_timeout: Maximum seconds allowed for a single clone attempt. If exceeded, the attempt is considered failed and retried.
        cancel_event: Optional threading.Event which, when set, causes an early abort before starting a new attempt.

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
            logger.info(
                "Cancellation event set before attempt %d; aborting clone for '%s'", attempt + 1, repo_url
            )
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
            # Respect cancellation between attempts
            end_time = time.time() + sleep_for
            while time.time() < end_time:
                if cancel_event and cancel_event.is_set():
                    logger.info("Cancellation detected during backoff; aborting further retries.")
                    return False
                time.sleep(0.05)  # granularity for responsive cancellation
    return False  # Defensive fallback


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


# Now initialize root_agent after function definitions
root_agent = Agent(
    model=settings.model,
    name='root_agent',
    description='Tells the current time and current weather in a specified city.',
    instruction='You are a helpful assistant that tells the current time and current weather in cities.',
    tools=[get_uaa_version, install_uaa],
)

if __name__ == '__main__':
    # Configure logging only when running as a script to avoid overriding host application logging.
    logging.basicConfig(
        level=settings.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info('Logger initialized (script execution).')
    # Only run the example clone when invoked directly.
    _example_clone()
