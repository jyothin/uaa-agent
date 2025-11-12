"""Diagnostics script to capture lint and test output to files.

Writes:
  diagnostics_output/ruff_stdout.txt
  diagnostics_output/ruff_stderr.txt
  diagnostics_output/pytest_result.txt
  diagnostics_output/env_info.txt
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(__file__), 'diagnostics_output')
os.makedirs(OUT_DIR, exist_ok=True)

def write(path: str, data: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)

def run_cmd(cmd: list[str], stdout_file: str, stderr_file: str) -> int:
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = proc.communicate()
        write(os.path.join(OUT_DIR, stdout_file), out or '')
        write(os.path.join(OUT_DIR, stderr_file), err or '')
        return proc.returncode
    except Exception as e:  # fallback logging
        write(os.path.join(OUT_DIR, stderr_file), f"EXCEPTION: {e}\n")
        return 255

def capture_env():
    lines = [
        f"Timestamp: {datetime.utcnow().isoformat()}Z",
        f"Python: {platform.python_version()}",
        f"Executable: {sys.executable}",
        f"CWD: {os.getcwd()}",
    ]
    # Key env vars
    for key in ["UAA_MODEL", "UAA_REPO_URL", "LOG_LEVEL"]:
        lines.append(f"ENV {key}={os.getenv(key)}")
    write(os.path.join(OUT_DIR, 'env_info.txt'), "\n".join(lines))


def main():
    capture_env()
    ruff_rc = run_cmd([sys.executable, '-m', 'ruff', 'check', '.', '--verbose'], 'ruff_stdout.txt', 'ruff_stderr.txt')

    # Run pytest via subprocess to isolate any plugin/system-level early exits.
    pytest_rc = run_cmd([sys.executable, '-m', 'pytest', '-vv', '--maxfail=1'], 'pytest_result.txt', 'pytest_errors.txt')

    summary = f"Ruff exit: {ruff_rc}\nPytest exit: {pytest_rc}\n"
    write(os.path.join(OUT_DIR, 'summary.txt'), summary)
    print(summary)

if __name__ == '__main__':
    main()
