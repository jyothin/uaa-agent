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
    log_level: str
    uaa_repo_url: str
    uaa_base_url: str
    uaa_java_version: str

    @staticmethod
    def from_env() -> Settings:
        return Settings(
            model=os.getenv('MODEL', 'gemini-2.5-flash'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            uaa_repo_url=os.getenv('UAA_REPO_URL', 'https://github.com/cloudfoundry/uaa'),
            uaa_base_url=os.getenv('UAA_BASE_URL', 'http://localhost:8080/uaa'),
            uaa_java_version=os.getenv('UAA_JAVA_VERSION', '21.0.9-amzn'),
        )


settings = Settings.from_env()
