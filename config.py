"""Configuration loader for uaa-agent.

Loads environment variables optionally from a .env file using python-dotenv.
Provides a dataclass for structured access.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - fallback if dotenv not installed
    load_dotenv = None  # type: ignore

if load_dotenv is not None:
    # Load .env if present; do not override existing environment variables.
    load_dotenv(override=False)


@dataclass(frozen=True)
class Settings:
    model: str
    repo_url: str
    log_level: str

    @staticmethod
    def from_env() -> Settings:
        return Settings(
            model=os.getenv('UAA_MODEL', 'gemini-2.5-flash'),
            repo_url=os.getenv('UAA_REPO_URL', 'https://github.com/cloudfoundry/uaa'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
        )


settings = Settings.from_env()
