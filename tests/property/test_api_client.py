"""Property-based tests for API client correctness.

Feature: python-mcp-server, Property 3: API Client Correctness
Validates: Requirements 3.2, 3.3, 3.4
"""

from unittest.mock import Mock, patch

import httpx
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from src.api.client import NPSAPIClient, NPSAPIError
from src.api.rate_limit import RateLimiter

# Property 3: API Client Correctness
# For any NPS API request, the API client should include proper authentication headers,
# respect rate limiting constraints, and handle errors gracefully with structured responses


@settings(max_examples=100)
@given(
    api_key=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    endpoint=st.text(min_size=1, max_size=50).filter(lambda x: "/" in x or len(x) > 0),
)
def test_api_client_includes_authentication_headers(api_key, endpoint):
    """
    Property: For any API key and endpoint, the client should include proper authentication headers.

    If an API key is provided, it should be included in the X-Api-Key header.
    """
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        # Create client with the given API key
        _ = NPSAPIClient(
            api_key=api_key, enable_rate_limiting=False, enable_retry=False
        )

        # Verify that the client was created with proper headers
        call_args = mock_client_class.call_args
        headers = call_args.kwargs.get("headers", {})

        if api_key:
            assert "X-Api-Key" in headers, "API key should be in headers when provided"
            assert (
                headers["X-Api-Key"] == api_key
            ), "API key should match provided value"
        else:
            assert (
                "X-Api-Key" not in headers
            ), "API key should not be in headers when not provided"


@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    requests_per_hour=st.integers(min_value=1, max_value=10000),
    num_requests=st.integers(min_value=1, max_value=10),
)
def test_api_client_respects_rate_limiting(requests_per_hour, num_requests):
    """
    Property: For any rate limit configuration, the client should respect rate limiting constraints.

    The rate limiter should prevent exceeding the configured requests per hour.
    """
    # Create a rate limiter with the given configuration
    rate_limiter = RateLimiter(requests_per_hour=requests_per_hour)

    # Acquire tokens for multiple requests
    tokens_acquired = 0
    for _ in range(num_requests):
        # Try to acquire without blocking (to avoid test timeouts)
        if rate_limiter.acquire(tokens=1, block=False):
            tokens_acquired += 1

    # Verify that we didn't exceed the available tokens
    # The initial token count should be equal to requests_per_hour
    assert tokens_acquired <= requests_per_hour, "Should not exceed rate limit"

    # Verify that the remaining tokens are correct
    remaining = rate_limiter.get_available_tokens()
    expected_remaining = requests_per_hour - tokens_acquired
    assert (
        abs(remaining - expected_remaining) < 1.0
    ), "Remaining tokens should match expected value"


@settings(max_examples=100)
@given(
    status_code=st.sampled_from([400, 401, 403, 404, 429, 500, 502, 503, 504]),
    error_message=st.text(min_size=1, max_size=100),
)
def test_api_client_handles_http_errors_gracefully(status_code, error_message):
    """
    Property: For any HTTP error status code, the client should handle errors gracefully.

    HTTP errors should be converted to NPSAPIError with structured error information.
    """
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {"message": error_message}
        mock_response.text = error_message
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=Mock(url="https://test.com/api"),
            response=mock_response,
        )

        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test", enable_rate_limiting=False, enable_retry=False
        )

        # Attempt to make a request that will fail
        with pytest.raises(NPSAPIError) as exc_info:
            client.get("/test")

        # Verify that the error is properly structured
        error = exc_info.value
        assert error.status_code == status_code, "Error should include status code"
        assert error.error_type == "http_error", "Error type should be http_error"
        assert isinstance(error.message, str), "Error message should be a string"
        assert len(error.message) > 0, "Error message should not be empty"

        # Verify that the error can be converted to ErrorResponse
        error_response = error.to_error_response()
        assert error_response.error == "http_error"
        assert error_response.message == error.message
        assert error_response.details is not None
        assert "status_code" in error_response.details


@settings(max_examples=100)
@given(
    timeout_seconds=st.floats(min_value=0.1, max_value=60.0),
)
def test_api_client_handles_timeout_errors_gracefully(timeout_seconds):
    """
    Property: For any timeout configuration, the client should handle timeout errors gracefully.

    Timeout errors should be converted to NPSAPIError with appropriate error information.
    """
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = httpx.TimeoutException(
            "Request timed out"
        )
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test",
            timeout=timeout_seconds,
            enable_rate_limiting=False,
            enable_retry=False,
        )

        # Attempt to make a request that will timeout
        with pytest.raises(NPSAPIError) as exc_info:
            client.get("/test")

        # Verify that the error is properly structured
        error = exc_info.value
        assert error.error_type == "timeout_error", "Error type should be timeout_error"
        assert (
            "timeout" in error.message.lower() or "timed out" in error.message.lower()
        )
        assert isinstance(error.details, dict), "Error details should be a dictionary"


@settings(max_examples=100)
@given(
    network_error_message=st.text(min_size=1, max_size=100),
)
def test_api_client_handles_network_errors_gracefully(network_error_message):
    """
    Property: For any network error, the client should handle it gracefully.

    Network errors should be converted to NPSAPIError with appropriate error information.
    """
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = httpx.NetworkError(network_error_message)
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test", enable_rate_limiting=False, enable_retry=False
        )

        # Attempt to make a request that will fail with network error
        with pytest.raises(NPSAPIError) as exc_info:
            client.get("/test")

        # Verify that the error is properly structured
        error = exc_info.value
        assert error.error_type == "network_error", "Error type should be network_error"
        assert "network" in error.message.lower()
        assert isinstance(error.details, dict), "Error details should be a dictionary"


@settings(max_examples=50)
@given(
    max_retries=st.integers(min_value=0, max_value=5),
    should_succeed_on_attempt=st.integers(min_value=1, max_value=3),
)
def test_api_client_retry_logic_with_exponential_backoff(
    max_retries, should_succeed_on_attempt
):
    """
    Property: For any retry configuration, the client should implement exponential backoff.

    Failed requests should be retried up to max_retries times with exponential backoff.
    """
    assume(should_succeed_on_attempt <= max_retries + 1)

    # Mock time.sleep to avoid actual delays in tests
    with patch("time.sleep") as mock_sleep, patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()

        # Create a side effect that fails a few times then succeeds
        attempt_count = [0]

        def side_effect(*args, **kwargs):
            attempt_count[0] += 1
            if attempt_count[0] < should_succeed_on_attempt:
                # Fail with a retryable error (raise the exception directly)
                raise httpx.HTTPStatusError(
                    message="HTTP 503",
                    request=Mock(url="https://test.com/api"),
                    response=Mock(
                        status_code=503,
                        json=lambda: {"message": "Service unavailable"},
                        text="Service unavailable",
                    ),
                )
            else:
                # Succeed
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"data": []}
                mock_response.raise_for_status = Mock()
                return mock_response

        mock_client_instance.get.side_effect = side_effect
        mock_client_class.return_value = mock_client_instance

        # Create client with retry enabled
        client = NPSAPIClient(
            api_key="test",
            enable_rate_limiting=False,
            enable_retry=True,
            max_retries=max_retries,
        )

        # Make a request
        if should_succeed_on_attempt <= max_retries + 1:
            # Should succeed after retries
            result = client.get("/test")
            assert result == {"data": []}
            assert attempt_count[0] == should_succeed_on_attempt

            # Verify that sleep was called for retries (if any retries occurred)
            if should_succeed_on_attempt > 1:
                assert mock_sleep.call_count == should_succeed_on_attempt - 1
        else:
            # Should fail after exhausting retries
            with pytest.raises((NPSAPIError, httpx.HTTPStatusError)):
                client.get("/test")
            assert attempt_count[0] == max_retries + 1


@settings(max_examples=100)
@given(
    park_code=st.text(min_size=1, max_size=10).filter(lambda x: x.strip()),
    limit=st.integers(min_value=1, max_value=50),
)
def test_api_client_builds_correct_urls_and_params(park_code, limit):
    """
    Property: For any valid parameters, the client should build correct URLs and query parameters.

    The client should properly construct API endpoints and include query parameters.
    """
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test", enable_rate_limiting=False, enable_retry=False
        )

        # Make a request with parameters
        result = client.get_parks(parkCode=park_code, limit=limit)

        # Verify that the client was called with correct parameters
        assert mock_client_instance.get.called
        call_args = mock_client_instance.get.call_args

        # Check that params were passed
        params = call_args.kwargs.get("params", {})
        assert "parkCode" in params or "limit" in params

        # Verify result is properly parsed
        assert isinstance(result, dict)
        assert "data" in result
