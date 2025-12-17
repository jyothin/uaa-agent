"""UAA Server clone helpers.

This module contains utilities for cloning the UAA repository with retry logic.
"""

import logging
import os
import threading
import time

from git import Repo

logger = logging.getLogger(__name__)


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

        def _target() -> None:  # executed in worker thread
            try:
                Repo.clone_from(repo_url, destination_path)
            except Exception as exc:  # store exception to re-raise outside the thread
                captured["error"] = exc

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        # If no timeout specified, block until completion
        thread.join(timeout=attempt_timeout)
        if thread.is_alive():
            # Timed out; thread is still running. We cannot safely kill it; mark failure.
            logger.warning(
                "Clone attempt timed out after %.2f seconds for repo '%s'",
                attempt_timeout,
                repo_url,
            )
            return TimeoutError(f"clone attempt exceeded timeout {attempt_timeout}s")
        # Completed; check for exception
        return captured.get("error")

    # Base backoff can be tuned via environment without increasing argument count.
    base_backoff = float(os.getenv("UAA_CLONE_BASE_BACKOFF", "1.0"))
    attempt = 0
    # Loop attempts: initial attempt + retries until success or exhaustion
    while attempt <= max_retries:
        if cancel_event and cancel_event.is_set():
            logger.info("Clone cancelled before attempt %d.", attempt)
            return False
        try:
            if attempt_timeout is None:
                Repo.clone_from(repo_url, destination_path)
                logger.info("Repository cloned successfully to %s", destination_path)
                return True
            else:
                error = _attempt_clone()
                if error is None:
                    logger.info("Repository cloned successfully to %s", destination_path)
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
