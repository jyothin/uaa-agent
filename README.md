# UAA Agent
Repo for code that is a UAA (User Authentication & Authorization) Agent.

![CI Status](https://github.com/jyothin/uaa-agent/actions/workflows/ci.yml/badge.svg)
[![Coverage](https://codecov.io/gh/jyothin/uaa-agent/branch/dev/graph/badge.svg)](https://codecov.io/gh/jyothin/uaa-agent)

# Create your virtual env
```bash
source ./venv/bin/activate`
```

# Build
```bash
pip install -r requirements.txt
```

## Environment Variables

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

### Quick Start with .env

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

### Example

Either export variables inline or rely on `.env`:

```bash
# Inline export example
LOG_LEVEL=DEBUG MODEL=gemini-2.5-flash UAA_REPO_URL=https://github.com/cloudfoundry/uaa adk run uaa_agent 
```

## Testing

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

### Coverage Reporting

Local commands:

```bash
python -m coverage run -m pytest -q
python -m coverage report -m
python -m coverage html   # generates html files in htmlcov (replace html with xml to coverage.xml file)
```

The CI workflow enforces a minimum coverage threshold (currently **80%**). Adjust by editing the `--fail-under` value in `.github/workflows/ci.yml`.

The coverage badge uses Codecov (branch: `dev`). For private repositories set a `CODECOV_TOKEN` secret; public repos usually work without it. You can adjust badge branch by changing `branch/dev` in the badge URL.

## Clone Timeout & Cancellation

The `clone_repository` function supports optional per-attempt timeouts and cooperative cancellation:

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `attempt_timeout` | `float | None` | `None` | Max seconds allowed for a single clone attempt. If the underlying clone thread is still running after this duration the attempt is marked failed and retried. |
| `cancel_event` | `threading.Event | None` | `None` | When set before an attempt starts (or during backoff), aborts further cloning and returns `False` immediately. |

### Example Usage

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

### Behavior Details
* Timeout does not forcibly kill the underlying GitPython operation; instead the worker thread is allowed to continue (daemon) while the attempt is treated as failed. This avoids unsafe thread termination in Python.
* Cancellation is checked before each attempt and during the backoff waiting window for responsive aborts.
* A successful attempt short-circuits retries.
* Final return value is `True` on success, `False` on exhaustion, timeout-only failures, or cancellation.
* Backoff timing is controlled via `UAA_CLONE_BASE_BACKOFF` environment variable (default `1.0`).

### When to Use
* Use `attempt_timeout` when network stalls or slow endpoints would otherwise block the process indefinitely.
* Use `cancel_event` to allow a higher-level controller (e.g., UI, orchestration layer) to stop long-running retries.

## pre-commit Hooks

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


### Notes
* If `UAA_REPO_URL` is unreachable the clone logic will retry with exponential backoff (see `clone_repository`).
* Set `LOG_LEVEL=DEBUG` to inspect retry behavior and repository cloning details.

# Test
[API Testing (curl)](https://google.github.io/adk-docs/deploy/gke/#api-testing-curl_1)

# Run
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

# What can the agent do?

- Clone a UAA repository in a local path
- Set the Java Version
- Clean the Project
- Set the 'admin' client's client secret
- Set the product logo
- Set the square logo
- Check if SSL certificates exist
- Create a server side SSL certificate
- Build/Assemble the Project
- Run the UAA server in detached mode
- Check if a UAA server is running
- Create a token for a client
- Create an identify zone
- List identity zones
