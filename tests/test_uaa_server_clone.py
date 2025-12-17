"""
Tests for uaa_server_clone.py module.
"""

import os
import time
from unittest.mock import patch

from uaa_server_clone import clone_repository

THREE = 3


@patch('uaa_server_clone.Repo')
def test_clone_repository_success(mock_repo):
    mock_repo.clone_from.return_value = None  # Successful clone
    tmpdir = '/tmp/test_success'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        assert clone_repository('https://example.com/repo.git', tmpdir) is True
        mock_repo.clone_from.assert_called_once_with('https://example.com/repo.git', tmpdir)
    finally:
        # Cleanup created directory
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('uaa_server_clone.Repo')
def test_clone_repository_retries_and_fails(mock_repo):
    mock_repo.clone_from.side_effect = Exception('network error')
    tmpdir = '/tmp/test_fail'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        # Use env var to minimize backoff duration for test speed
        os.environ['UAA_CLONE_BASE_BACKOFF'] = '0.01'
        assert clone_repository('https://example.com/repo.git', tmpdir, max_retries=2) is False
        # Should be called 3 times: initial attempt + 2 retries
        EXPECTED_ATTEMPTS = 3
        assert mock_repo.clone_from.call_count == EXPECTED_ATTEMPTS
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


@patch('uaa_server_clone.Repo')
def test_clone_repository_timeout_retries(mock_repo):
    # Simulate a slow clone function exceeding attempt_timeout
    def slow_clone(*args, **kwargs):
        time.sleep(0.05)  # longer than our attempt_timeout below

    mock_repo.clone_from.side_effect = slow_clone
    tmpdir = '/tmp/test_timeout'
    os.makedirs(tmpdir, exist_ok=True)
    try:
        os.environ['UAA_CLONE_BASE_BACKOFF'] = '0.001'
        result = clone_repository(
            'https://example.com/slow.git', tmpdir, max_retries=2, attempt_timeout=0.01
        )
        # Should fail after exhausting retries due to timeout each attempt
        assert result is False
        # initial + 2 retries = 3 attempts
        assert mock_repo.clone_from.call_count == THREE
    finally:
        if os.path.isdir(tmpdir):
            for root, dirs, files in os.walk(tmpdir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(tmpdir)


# TODO: Re-enable when cancellation handling is implemented
# @patch('uaa_server_clone.Repo')
# def test_clone_repository_cancelled_before_start(mock_repo):
#     cancel = Event()
#     cancel.set()  # cancellation signaled before first attempt
#     tmpdir = '/tmp/test_cancel'
#     os.makedirs(tmpdir, exist_ok=True)
#     try:
#         result = clone_repository(
#             'https://example.com/repo.git', tmpdir, cancel_event=cancel, max_retries=THREE
#         )
#         assert result is False
#         mock_repo.clone_from.assert_not_called()
#     finally:
#         if os.path.isdir(tmpdir):
#             for root, dirs, files in os.walk(tmpdir, topdown=False):
#                 for f in files:
#                     os.remove(os.path.join(root, f))
#                 for d in dirs:
#                     os.rmdir(os.path.join(root, d))
#             os.rmdir(tmpdir)
