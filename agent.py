"""Agent module for interacting with UAA and cloning repositories.

Refinements:
 - Environment-driven configuration for model and repo URL.
 - Retry logic for git clone with exponential backoff.
 - Logging configured only when executed as a script (not on import).
"""

# Standard library imports
import logging
import os
import time
import tempfile  # secure temporary directory creation
from typing import Optional
from git import Repo

# Tool imports

# Application-specific imports
from google.adk.agents.llm_agent import Agent
from config import settings

logger = logging.getLogger(__name__)

# Goals
# 1. Get UAA server version
# 2. Install UAA server


 # root_agent initialization will occur after function definitions to ensure names are defined.

def get_uaa_version() -> str:
    """Get the current UAA server version"""
    return ""


def install_uaa(repo_url, destination_path) -> bool:
    """Install UAA server"""
    status = clone_repository(repo_url, destination_path)
    return status


def clone_repository(
    repo_url: str,
    destination_path: str,
    max_retries: int = 3,
    retry_backoff: float = 1.0,
) -> bool:
    """Clone a git repository to a destination path with retry logic.

    Args:
        repo_url: HTTPS (or SSH) URL of the repository to clone.
        destination_path: Filesystem path where the repo should be cloned.
        max_retries: Number of retry attempts on failure.
        retry_backoff: Initial backoff delay in seconds (exponential growth).

    Returns:
        True if clone succeeds, False otherwise.
    """
    attempt = 0
    while attempt <= max_retries:
        try:
            Repo.clone_from(repo_url, destination_path)
            logger.info("Repository cloned successfully to %s", destination_path)
            return True
        except Exception as e:
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
            sleep_for = retry_backoff * (2 ** (attempt - 1))
            logger.warning(
                "Clone attempt %d for '%s' failed: %s. Retrying in %.2f seconds...",
                attempt,
                repo_url,
                e,
                sleep_for,
            )
            time.sleep(sleep_for)
    # Fallback (shouldn't be reached due to loop logic); defensive return.
    return False

def _example_clone(repo_url: str | None = None) -> None:
    """Example: clone UAA repo into an ephemeral temporary directory under /tmp.

    The directory is cleaned up automatically when the context exits.
    Repo URL can be overridden via env UAA_REPO_URL.
    """
    repo_url = repo_url or os.getenv("UAA_REPO_URL", "https://github.com/cloudfoundry/uaa")
    with tempfile.TemporaryDirectory(prefix="uaa_repo_", dir="/tmp") as tmpdir:
        logger.info("Cloning repository '%s' into temporary dir: %s", repo_url, tmpdir)
        success = clone_repository(repo_url, tmpdir)
        if success:
            try:
                logger.info("Clone completed. Contents: %s", os.listdir(tmpdir))
            except Exception:
                logger.debug("Could not list contents of %s", tmpdir)
        else:
            logger.warning("Clone failed; temporary directory will still be cleaned up.")

# Now initialize root_agent after function definitions
root_agent = Agent(
    model=settings.model,
    name='root_agent',
    description='Tells the current time and current weather in a specified city.',
    instruction='You are a helpful assistant that tells the current time and current weather in cities.',
    tools=[get_uaa_version, install_uaa],
)

if __name__ == "__main__":
    # Configure logging only when running as a script to avoid overriding host application logging.
    logging.basicConfig(
        level=settings.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("Logger initialized (script execution).")
    # Only run the example clone when invoked directly.
    _example_clone()
