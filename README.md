# UAA Agent
Repo for code that is a UAA (User Authentication & Authorization) Agent.

# Create your virtual env
`$> source ./venv/bin/activate`

# Build
`$> pip install -r requirements.txt`

## Environment Variables

The agent behavior can be customized via the following environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `UAA_MODEL` | `gemini-2.5-flash` | Model name passed when constructing the root `Agent` (loaded via `config.py`). |
| `UAA_REPO_URL` | `https://github.com/cloudfoundry/uaa` | Overrides repository URL used by `_example_clone` helper. |
| `LOG_LEVEL` | `INFO` | Controls logging verbosity when running `agent.py` as a script. Standard levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`. |

The file `config.py` loads these values on import. If a local `.env` file exists it will be read automatically (using `python-dotenv`) without overriding already-set environment variables.

### Quick Start with .env

1. Copy the example file:
	```bash
	cp .env.example .env
	```
2. Adjust values in `.env` as needed.
3. Run the agent script:
	```bash
	python agent.py
	```

### Example

Either export variables inline or rely on `.env`:

```bash
# Inline export example
LOG_LEVEL=DEBUG UAA_MODEL=gemini-2.5-flash UAA_REPO_URL=https://github.com/cloudfoundry/uaa python agent.py
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


### Notes
* If `UAA_REPO_URL` is unreachable the clone logic will retry with exponential backoff (see `clone_repository`).
* Set `LOG_LEVEL=DEBUG` to inspect retry behavior and repository cloning details.


