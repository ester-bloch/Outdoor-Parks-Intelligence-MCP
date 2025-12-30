"""Unit tests for NPS API client.

Tests authentication, rate limiting, error handling, and retry logic.
Requirements: 3.2, 3.3, 3.4
"""

import time
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from src.api.client import NPSAPIClient, NPSAPIError
from src.api.rate_limit import RateLimiter
from src.api.retry import RetryConfig, calculate_backoff_delay, should_retry_error


class TestNPSAPIClient:
    """Test suite for NPSAPIClient."""

    def test_client_initialization_with_api_key(self):
        """Test that client initializes with API key in headers."""
        with patch("httpx.Client") as mock_client_class:
            client = NPSAPIClient(
                api_key="test-key", enable_rate_limiting=False, enable_retry=False
            )

            # Verify client was created with correct headers
            call_args = mock_client_class.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "X-Api-Key" in headers
            assert headers["X-Api-Key"] == "test-key"

    def test_client_initialization_without_api_key(self):
        """Test that client initializes without API key."""
        with patch("httpx.Client") as mock_client_class:
            client = NPSAPIClient(
                api_key=None, enable_rate_limiting=False, enable_retry=False
            )

            # Verify client was created without API key header
            call_args = mock_client_class.call_args
            headers = call_args.kwargs.get("headers", {})
            assert "X-Api-Key" not in headers

    def test_client_uses_custom_base_url(self):
        """Test that client uses custom base URL."""
        custom_url = "https://custom.api.com/v2"
        with patch("httpx.Client") as mock_client_class:
            client = NPSAPIClient(
                base_url=custom_url, enable_rate_limiting=False, enable_retry=False
            )

            call_args = mock_client_class.call_args
            assert call_args.kwargs.get("base_url") == custom_url

    def test_build_url_with_leading_slash(self):
        """Test URL building with leading slash."""
        with patch("httpx.Client"):
            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            url = client._build_url("/parks")
            assert url.endswith("/parks")

    def test_build_url_without_leading_slash(self):
        """Test URL building without leading slash."""
        with patch("httpx.Client"):
            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            url = client._build_url("parks")
            assert url.endswith("/parks")

    def test_successful_get_request(self):
        """Test successful GET request."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": [{"id": "1"}]}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            result = client.get("/parks")

            assert result == {"data": [{"id": "1"}]}
            mock_client_instance.get.assert_called_once()

    def test_http_error_handling(self):
        """Test HTTP error handling."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "Not found"}
            mock_response.text = "Not found"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="HTTP 404",
                request=Mock(url="https://test.com/api"),
                response=mock_response,
            )
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.status_code == 404
            assert error.error_type == "http_error"

    def test_timeout_error_handling(self):
        """Test timeout error handling."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.TimeoutException(
                "Request timed out"
            )
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "timeout_error"
            assert (
                "timed out" in error.message.lower()
                or "timeout" in error.message.lower()
            )

    def test_network_error_handling(self):
        """Test network error handling."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.NetworkError("Network error")
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "network_error"
            assert "network" in error.message.lower()

    def test_get_parks_method(self):
        """Test get_parks convenience method."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            result = client.get_parks(stateCode="CA", limit=10)

            assert result == {"data": []}
            call_args = mock_client_instance.get.call_args
            params = call_args.kwargs.get("params", {})
            assert "stateCode" in params
            assert "limit" in params

    def test_get_park_by_code_method(self):
        """Test get_park_by_code convenience method."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            result = client.get_park_by_code("yose")

            assert result == {"data": []}
            call_args = mock_client_instance.get.call_args
            params = call_args.kwargs.get("params", {})
            assert params.get("parkCode") == "yose"

    def test_context_manager(self):
        """Test client as context manager."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            with NPSAPIClient(enable_rate_limiting=False, enable_retry=False) as client:
                assert client is not None

            mock_client_instance.close.assert_called_once()

    def test_error_response_conversion(self):
        """Test NPSAPIError to ErrorResponse conversion."""
        error = NPSAPIError(
            message="Test error",
            status_code=500,
            error_type="test_error",
            details={"key": "value"},
        )

        error_response = error.to_error_response()
        assert error_response.error == "test_error"
        assert error_response.message == "Test error"
        assert error_response.details["status_code"] == 500
        assert error_response.details["key"] == "value"


class TestRateLimiter:
    """Test suite for RateLimiter."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_hour=1000)
        assert limiter.requests_per_hour == 1000
        assert limiter.tokens == 1000

    def test_acquire_single_token(self):
        """Test acquiring a single token."""
        limiter = RateLimiter(requests_per_hour=1000)
        result = limiter.acquire(tokens=1, block=False)
        assert result is True
        assert limiter.tokens < 1000

    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens."""
        limiter = RateLimiter(requests_per_hour=1000)
        result = limiter.acquire(tokens=10, block=False)
        assert result is True
        assert limiter.tokens == 990

    def test_acquire_exceeds_available_tokens(self):
        """Test acquiring more tokens than available (non-blocking)."""
        limiter = RateLimiter(requests_per_hour=10)
        limiter.acquire(tokens=10, block=False)
        result = limiter.acquire(tokens=1, block=False)
        assert result is False

    def test_token_refill(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(requests_per_hour=3600)  # 1 token per second
        limiter.acquire(tokens=10, block=False)
        initial_tokens = limiter.get_available_tokens()

        # Wait a bit for tokens to refill
        time.sleep(0.1)
        refilled_tokens = limiter.get_available_tokens()

        assert refilled_tokens > initial_tokens

    def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(requests_per_hour=1000)
        limiter.acquire(tokens=500, block=False)
        assert limiter.tokens < 1000

        limiter.reset()
        assert limiter.tokens == 1000


class TestRetryLogic:
    """Test suite for retry logic."""

    def test_calculate_backoff_delay(self):
        """Test exponential backoff calculation."""
        delay = calculate_backoff_delay(
            attempt=0, initial_delay=1.0, max_delay=60.0, exponential_base=2.0
        )
        assert delay == 1.0

        delay = calculate_backoff_delay(
            attempt=1, initial_delay=1.0, max_delay=60.0, exponential_base=2.0
        )
        assert delay == 2.0

        delay = calculate_backoff_delay(
            attempt=2, initial_delay=1.0, max_delay=60.0, exponential_base=2.0
        )
        assert delay == 4.0

    def test_backoff_delay_max_limit(self):
        """Test that backoff delay respects max limit."""
        delay = calculate_backoff_delay(
            attempt=10, initial_delay=1.0, max_delay=10.0, exponential_base=2.0
        )
        assert delay == 10.0

    def test_should_retry_network_error(self):
        """Test that network errors trigger retry."""
        error = httpx.NetworkError("Network error")
        assert should_retry_error(error, (429, 500, 502, 503, 504)) is True

    def test_should_retry_timeout_error(self):
        """Test that timeout errors trigger retry."""
        error = httpx.TimeoutException("Timeout")
        assert should_retry_error(error, (429, 500, 502, 503, 504)) is True

    def test_should_retry_http_status_error(self):
        """Test that specific HTTP status codes trigger retry."""
        mock_response = Mock()
        mock_response.status_code = 503
        error = httpx.HTTPStatusError(
            message="Service unavailable",
            request=Mock(),
            response=mock_response,
        )
        assert should_retry_error(error, (429, 500, 502, 503, 504)) is True

    def test_should_not_retry_http_status_error(self):
        """Test that non-retryable HTTP status codes don't trigger retry."""
        mock_response = Mock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError(
            message="Not found",
            request=Mock(),
            response=mock_response,
        )
        assert should_retry_error(error, (429, 500, 502, 503, 504)) is False

    def test_retry_config_initialization(self):
        """Test retry configuration initialization."""
        config = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
        )
        assert config.max_retries == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0

    def test_retry_config_default_status_codes(self):
        """Test default retry status codes."""
        config = RetryConfig()
        assert 429 in config.retry_on_status_codes
        assert 500 in config.retry_on_status_codes
        assert 502 in config.retry_on_status_codes
        assert 503 in config.retry_on_status_codes
        assert 504 in config.retry_on_status_codes


class TestAPIClientIntegration:
    """Integration tests for API client with rate limiting and retry."""

    def test_client_with_rate_limiting_enabled(self):
        """Test that rate limiting is properly integrated."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(
                enable_rate_limiting=True,
                requests_per_hour=100,
                enable_retry=False,
            )

            # Make multiple requests
            for _ in range(5):
                result = client.get("/parks")
                assert result == {"data": []}

            # Verify rate limiter has consumed tokens
            assert client.rate_limiter is not None
            assert client.rate_limiter.get_available_tokens() < 100

    def test_client_without_rate_limiting(self):
        """Test that rate limiting can be disabled."""
        with patch("httpx.Client"):
            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            assert client.rate_limiter is None

    def test_client_with_retry_enabled(self):
        """Test that retry logic is properly integrated."""
        from src.api.retry import RetryableHTTPClient

        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(
                enable_rate_limiting=False,
                enable_retry=True,
                max_retries=3,
            )

            # Verify client is wrapped with retry logic
            assert isinstance(client.client, RetryableHTTPClient)

    def test_client_without_retry(self):
        """Test that retry logic can be disabled."""
        from src.api.retry import RetryableHTTPClient

        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            # Verify client is not wrapped
            assert not isinstance(client.client, RetryableHTTPClient)

    def test_client_retry_on_transient_error(self):
        """Test that client retries on transient errors."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()

            # Create mock responses
            mock_response_fail = Mock()
            mock_response_fail.status_code = 503
            mock_response_fail.text = "Service unavailable"
            mock_response_fail.json.return_value = {"message": "Service unavailable"}

            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"data": []}
            mock_response_success.raise_for_status = Mock()

            # First call fails with 503, second succeeds
            call_count = [0]

            def get_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call raises HTTPStatusError
                    raise httpx.HTTPStatusError(
                        message="Service unavailable",
                        request=Mock(url="https://test.com/api"),
                        response=mock_response_fail,
                    )
                else:
                    # Second call succeeds
                    return mock_response_success

            mock_client_instance.get.side_effect = get_side_effect
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(
                enable_rate_limiting=False, enable_retry=True, max_retries=2
            )

            result = client.get("/parks")
            assert result == {"data": []}
            assert call_count[0] == 2  # Should have retried once

    def test_client_exhausts_retries(self):
        """Test that client exhausts retries and raises error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_response.json.return_value = {"message": "Service unavailable"}

            # Always raise HTTPStatusError
            def get_side_effect(*args, **kwargs):
                raise httpx.HTTPStatusError(
                    message="Service unavailable",
                    request=Mock(url="https://test.com/api"),
                    response=mock_response,
                )

            mock_client_instance.get.side_effect = get_side_effect
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(
                enable_rate_limiting=False, enable_retry=True, max_retries=2
            )

            with pytest.raises(NPSAPIError):
                client.get("/parks")

            # Should have tried 3 times (initial + 2 retries)
            assert mock_client_instance.get.call_count == 3

    def test_global_client_instance(self):
        """Test global client instance management."""
        from src.api.client import _client, close_client, get_client

        with patch("httpx.Client"):
            # Get client instance
            client1 = get_client()
            assert client1 is not None

            # Get same instance again
            client2 = get_client()
            assert client1 is client2

            # Close client
            close_client()

            # Get new instance after closing
            client3 = get_client()
            assert client3 is not client1

    def test_client_close_with_retry_wrapper(self):
        """Test closing client when wrapped with retry logic."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=True)
            client.close()

            # Verify the underlying client was closed
            mock_client_instance.close.assert_called_once()

    def test_get_alerts_method(self):
        """Test get_alerts convenience method."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            result = client.get_alerts(park_code="yose")

            assert result == {"data": []}
            call_args = mock_client_instance.get.call_args
            params = call_args.kwargs.get("params", {})
            assert params.get("parkCode") == "yose"

    def test_get_visitor_centers_method(self):
        """Test get_visitor_centers convenience method."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            result = client.get_visitor_centers(park_code="yose")

            assert result == {"data": []}

    def test_get_campgrounds_method(self):
        """Test get_campgrounds convenience method."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            result = client.get_campgrounds(park_code="yose")

            assert result == {"data": []}

    def test_get_events_method(self):
        """Test get_events convenience method."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)
            result = client.get_events(park_code="yose")

            assert result == {"data": []}
