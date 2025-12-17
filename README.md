# UAA Agent

Repo for code that is a UAA (User Authentication & Authorization) Agent.

![CI Status](https://github.com/jyothin/uaa-agent/actions/workflows/ci.yml/badge.svg)
[![Coverage](https://codecov.io/gh/jyothin/uaa-agent/branch/dev/graph/badge.svg)](https://codecov.io/gh/jyothin/uaa-agent)

## Create your virtual env

```bash
source ./venv/bin/activate`
```

## Build

```bash
pip install -r requirements.txt
```

### Environment Variables

The agent behavior can be customized via the following environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `MODEL` | `gemini-2.5-flash` | Model name passed when constructing the root `Agent` (loaded via `config.py`). |
| `UAA_REPO_URL` | `https://github.com/cloudfoundry/uaa` | Overrides repository URL used by `_example_clone` helper. |
| `LOG_LEVEL` | `INFO` | Controls logging verbosity when running `agent.py` as a script. Standard levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `UAA_CLONE_BASE_BACKOFF` | `1.0` | Base seconds for exponential backoff between clone retries in `clone_repository` (used when reducing args). Set lower (e.g. `0.01`) for faster test cycles. |
| `UAA_BASE_URL` | `http://localhost:8080/uaa` | Base URL for the UAA server. |
| `UAA_JAVA_VERSION` | `21.0.9-amzn` | Java version should be at least 21. |

The file `config.py` loads these values on import. If a local `.env` file exists it will be read automatically (using `python-dotenv`) without overriding already-set environment variables.

#### Quick Start with .env

1. Copy the example file:

    ```bash
    cp .env.example .env
    ```

2. Adjust values in `.env` as needed.

3. Run the agent:

    ```bash
    cd ..
    adk run uaa_agent
    ```

#### Example

Either export variables inline or rely on `.env`:

```bash
# Inline export example
LOG_LEVEL=DEBUG MODEL=gemini-2.5-flash UAA_REPO_URL=https://github.com/cloudfoundry/uaa adk run uaa_agent 
```

### Testing

Run the test suite (uses `pytest`):

```bash
python -m pytest
```

Run tests quietly:

```bash
python -m pytest -q
```

Include coverage (requires `coverage` if you add it later):

```bash
python -m pytest --maxfail=1 --disable-warnings -q
```

Recommended local pre-flight (lint + tests):

```bash
python -m ruff check . && python -m pytest -q
```

Target a specific test file or function:

```bash
python -m pytest tests/test_agent.py::test_clone_repository_success -q
```

If you create a virtual environment manually, ensure it is activated before running the commands above.

#### Coverage Reporting

Local commands:

```bash
python -m coverage run -m pytest -q
python -m coverage report -m
python -m coverage html   # generates html files in htmlcov (replace html with xml to coverage.xml file)
```

The CI workflow enforces a minimum coverage threshold (currently **80%**). Adjust by editing the `--fail-under` value in `.github/workflows/ci.yml`.

The coverage badge uses Codecov (branch: `dev`). For private repositories set a `CODECOV_TOKEN` secret; public repos usually work without it. You can adjust badge branch by changing `branch/dev` in the badge URL.

### Clone Timeout & Cancellation

The `clone_repository` function supports optional per-attempt timeouts and cooperative cancellation:

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `attempt_timeout` | `float | None` | Max seconds allowed for a single clone attempt. If the underlying clone thread is still running after this duration the attempt is marked failed and retried. |
| `cancel_event` | `threading.Event | None` | When set before an attempt starts (or during backoff), aborts further cloning and returns `False` immediately. |

#### Example Usage

```python
import threading
from agent import clone_repository

cancel = threading.Event()

# Trigger cancellation from somewhere else (e.g., user action or timeout watchdog)
# cancel.set()

success = clone_repository(
 repo_url="https://github.com/cloudfoundry/uaa",
 destination_path="/tmp/uaa_clone",
 max_retries=2,
 retry_backoff=0.5,
 attempt_timeout=10.0,  # each attempt capped at 10s
 cancel_event=cancel,    # can be signaled externally
)
print("Clone succeeded?", success)
```

#### Behavior Details

* Timeout does not forcibly kill the underlying GitPython operation; instead the worker thread is allowed to continue (daemon) while the attempt is treated as failed. This avoids unsafe thread termination in Python.
* Cancellation is checked before each attempt and during the backoff waiting window for responsive aborts.
* A successful attempt short-circuits retries.
* Final return value is `True` on success, `False` on exhaustion, timeout-only failures, or cancellation.
* Backoff timing is controlled via `UAA_CLONE_BASE_BACKOFF` environment variable (default `1.0`).

#### When to Use

* Use `attempt_timeout` when network stalls or slow endpoints would otherwise block the process indefinitely.
* Use `cancel_event` to allow a higher-level controller (e.g., UI, orchestration layer) to stop long-running retries.

### pre-commit Hooks

Automated lint & formatting can run before each commit using `pre-commit`.

Install hooks (after installing dev dependencies):

```bash
pre-commit install
```

Run on all files (first time or after adding new hooks):

```bash
pre-commit run --all-files
```

Hooks configured in `.pre-commit-config.yaml`:

* Ruff lint (`ruff check`) – style/import/order & quality rules.
* Ruff format – code formatting.
* Basic hygiene: end-of-file-fixer, trailing whitespace, YAML/TOML syntax, large file guard.

If CI fails due to lint issues, run the above commands locally and re-commit.

#### Notes

* If `UAA_REPO_URL` is unreachable the clone logic will retry with exponential backoff (see `clone_repository`).
* Set `LOG_LEVEL=DEBUG` to inspect retry behavior and repository cloning details.

## Test

[API Testing (curl)](https://google.github.io/adk-docs/deploy/gke/#api-testing-curl_1)

## Run

Go to the parent directory under which you see the `uaa_agent` folder

Run as a CLI

```bash
cd ..
adk run uaa_agent
```

Run as a webapp

```bash
adk web --port 8000
```

## What can the agent do?

* Clone a UAA repository in a local path
* Set the Java Version
* Clean the Project
* Set the 'admin' client's client secret
* Set the product logo
* Set the square logo
* Check if SSL certificates exist
* Create a server side SSL certificate
* Build/Assemble the Project
* Run the UAA server in detached mode
* Check if a UAA server is running
* Create a token for a client
* Create an identify zone
* List identity zones

## Module Overview

This agent composes several focused Python modules. These are the project-specific files imported by `agent.py` and how they fit together:

- [config.py](config.py): Loads environment-driven settings via `.env` (if present) and exposes `settings` (model, log level, UAA repo URL, base URL, Java version).
- [uaa_server_clone.py](uaa_server_clone.py): Reliable Git clone utilities with retry/backoff and optional per-attempt timeout. Exported: `clone_repository()`.
- [uaa_server_manager.py](uaa_server_manager.py): Local UAA server lifecycle and Java/SDKMAN helpers.
    - Java helpers: `sdk_use_java_version()`, `sdk_set_sdkmanrc_file()`, `get_java_version()`, `get_java_version_from_sdkmanrc()`
    - Build/run: `assemble_uaa()`, `build_uaa()`, `run_uaa_detached()`, `clean_uaa()`
    - Process/network: `wait_for_port()`, `stop_uaa()`
    - Certificates: `check_certificates_exist()`, `generate_certificate()`
- [uaa_server_information.py](uaa_server_information.py): HTTP client for UAA Server Information endpoints (e.g., `/info`, OpenID discovery, passcode, autologin). Exported: `UAAServerInformationClient`.
- [uaa_admin_config.py](uaa_admin_config.py): Programmatic updates to `scripts/boot/uaa.yml` for admin client secret and `login.branding` values (logos, colors, links, company/product names, footer text/links).
- [uaa_identity_zones.py](uaa_identity_zones.py): HTTP client for Identity Zones (`/identity-zones`) with class-level token.
    - Token management: `set_token_for_uaa_identity_zones_client(token)` sets `UAAIdentityZonesClient.token`.
    - Operations: `create_an_identity_zone()`, `get_identity_zone()`, `get_all_identity_zones()`, `update_identity_zone()`.
- [uaa_token.py](uaa_token.py): Client Credentials Grant flow for tokens (`/oauth/token`). Exported: `UAAClientCredentialsGrantClient` with `create_without_authorization()`; handles connection errors and 400 Bad Request with descriptive messages.

How `agent.py` uses these modules:

- Wires the modules above into tools/actions exposed by the ADK `Agent` to orchestrate clone → build/assemble → run → configure → call APIs.
- Uses settings from `config.py` and wraps server operations from `uaa_server_manager.py` (build/run/stop, certificates, Java).
- Delegates YAML edits to `uaa_admin_config.py` and external API calls to `uaa_server_information.py`, `uaa_identity_zones.py`, and `uaa_token.py`.

Notes and patterns:

- Identity Zones token is a class variable on `UAAIdentityZonesClient`; prefer setting it via `set_token_for_uaa_identity_zones_client()` for testability and consistent usage.
- All HTTP clients return `{"error": ...}` dictionaries on connection issues; specific HTTP errors like 401/404/400 are handled where useful.
- Build/run commands rely on SDKMAN (`sdk env`) and Gradle wrappers inside the cloned UAA repo.
