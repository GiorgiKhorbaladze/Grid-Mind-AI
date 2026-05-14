"""Tests for data_sources.utils.retry."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from data_sources.utils.retry import retry_with_backoff


class TestRetryWithBackoff:
    def test_success_on_first_try(self):
        call_count = 0

        @retry_with_backoff(max_retries=3)
        def always_works():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = always_works()
        assert result == "ok"
        assert call_count == 1

    def test_retries_on_failure_then_succeeds(self):
        attempts = []

        @retry_with_backoff(max_retries=3, backoff_base=0.01, jitter=False)
        def fails_twice():
            attempts.append(1)
            if len(attempts) < 3:
                raise ConnectionError("transient")
            return "recovered"

        result = fails_twice()
        assert result == "recovered"
        assert len(attempts) == 3

    def test_raises_after_max_retries_exhausted(self):
        @retry_with_backoff(max_retries=2, backoff_base=0.01, jitter=False)
        def always_fails():
            raise ConnectionError("permanent")

        with pytest.raises(RuntimeError, match="failed after 2 retries"):
            always_fails()

    def test_original_exception_chained(self):
        @retry_with_backoff(max_retries=1, backoff_base=0.01, jitter=False)
        def fail():
            raise ValueError("root cause")

        with pytest.raises(RuntimeError) as exc_info:
            fail()
        assert isinstance(exc_info.value.__cause__, ValueError)
        assert "root cause" in str(exc_info.value.__cause__)

    def test_only_specified_exceptions_caught(self):
        @retry_with_backoff(
            max_retries=3,
            backoff_base=0.01,
            jitter=False,
            exceptions=(ConnectionError,),
        )
        def raise_value_error():
            raise ValueError("not retried")

        with pytest.raises(ValueError, match="not retried"):
            raise_value_error()

    def test_sleep_called_between_retries(self):
        @retry_with_backoff(max_retries=2, backoff_base=1.0, jitter=False)
        def fail():
            raise ConnectionError("boom")

        with patch("data_sources.utils.retry.time.sleep") as mock_sleep:
            with pytest.raises(RuntimeError):
                fail()
        assert mock_sleep.call_count == 2
        # First backoff = 1.0**0 = 1.0, second = 1.0**1 = 1.0
        for call in mock_sleep.call_args_list:
            assert call.args[0] == pytest.approx(1.0, abs=0.01)

    def test_jitter_modifies_sleep_duration(self):
        sleep_times = []

        original_sleep = time.sleep

        def capture_sleep(t):
            sleep_times.append(t)

        @retry_with_backoff(max_retries=1, backoff_base=2.0, jitter=True)
        def fail():
            raise ConnectionError("boom")

        with patch("data_sources.utils.retry.time.sleep", side_effect=capture_sleep):
            with pytest.raises(RuntimeError):
                fail()

        assert len(sleep_times) == 1
        # With jitter, sleep is in [0.5 * base^0, 1.5 * base^0] = [0.5, 1.5]
        assert 0.4 <= sleep_times[0] <= 1.6
