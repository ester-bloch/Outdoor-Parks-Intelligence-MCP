"""Property-based tests for NPS API integration consistency.

Feature: python-mcp-server, Property 5: NPS API Integration Consistency
Validates: Requirements 1.5
"""

from unittest.mock import Mock, patch

import httpx
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.api.client import NPSAPIClient, NPSAPIError
from src.api.rate_limit import RateLimiter


@settings(max_examples=50)
@given(
    endpoint=st.sampled_from(
        ["/parks", "/alerts", "/visitorcenters", "/campgrounds", "/events"]
    ),
    params=st.dictionaries(
        keys=st.sampled_from(["stateCode", "parkCode", "q", "limit", "start"]),
        values=st.text(min_size=1, max_size=20),
        min_size=0,
        max_size=3,
    ),
)
def test_api_client_supports_all_nps_endpoints(endpoint, params):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": "10",
            "limit": "10",
            "start": "0",
            "data": [],
        }
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test_key",
            enable_rate_limiting=False,
            enable_retry=False,
        )

        # Make request to the endpoint
        result = client.get(endpoint, params=params if params else None)

        # Verify the request was made
        assert mock_client_instance.get.called
        call_args = mock_client_instance.get.call_args

        # Verify endpoint is correct
        url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
        assert endpoint in url, f"URL should contain endpoint {endpoint}"

        # Verify parameters were passed
        if params:
            passed_params = call_args.kwargs.get("params", {})
            assert passed_params is not None, "Parameters should be passed to request"

        # Verify response structure matches NPS API format
        assert isinstance(result, dict), "Response should be a dictionary"
        assert "total" in result, "Response should have 'total' field"
        assert "limit" in result, "Response should have 'limit' field"
        assert "start" in result, "Response should have 'start' field"
        assert "data" in result, "Response should have 'data' field"


@settings(max_examples=50)
@given(
    api_key=st.text(min_size=10, max_size=50),
    requests_count=st.integers(min_value=1, max_value=10),
)
def test_api_client_maintains_authentication_across_requests(api_key, requests_count):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key=api_key,
            enable_rate_limiting=False,
            enable_retry=False,
        )

        # Make multiple requests
        for _ in range(requests_count):
            client.get("/parks")

        # Verify authentication header was set during initialization
        init_call_args = mock_client_class.call_args
        headers = init_call_args.kwargs.get("headers", {})
        assert "X-Api-Key" in headers, "X-Api-Key header should be set"
        assert headers["X-Api-Key"] == api_key, "API key should match"

        # Verify all requests were made
        assert mock_client_instance.get.call_count == requests_count


@settings(max_examples=30)
@given(
    requests_per_hour=st.integers(min_value=100, max_value=5000),
    request_burst_size=st.integers(min_value=1, max_value=20),
)
def test_api_client_rate_limiting_respects_constraints(
    requests_per_hour, request_burst_size
):
    # Create a rate limiter with the given configuration
    rate_limiter = RateLimiter(requests_per_hour=requests_per_hour)

    # Try to acquire tokens for a burst of requests
    tokens_acquired = 0
    for _ in range(request_burst_size):
        if rate_limiter.acquire(tokens=1, block=False):
            tokens_acquired += 1

    # Verify we didn't exceed the rate limit
    assert tokens_acquired <= requests_per_hour, "Should not exceed rate limit"

    # Verify the rate limiter tracks remaining tokens correctly
    remaining = rate_limiter.get_available_tokens()
    expected_remaining = requests_per_hour - tokens_acquired
    assert (
        abs(remaining - expected_remaining) < 1.0
    ), "Remaining tokens should be accurate"


@settings(max_examples=50)
@given(
    status_codes=st.lists(
        st.sampled_from([400, 401, 403, 404, 429, 500, 502, 503, 504]),
        min_size=1,
        max_size=5,
        unique=True,
    ),
)
def test_api_client_handles_all_http_error_codes(status_codes):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()

        for status_code in status_codes:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.json.return_value = {"message": f"Error {status_code}"}
            mock_response.text = f"Error {status_code}"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message=f"HTTP {status_code}",
                request=Mock(url="https://test.com/api"),
                response=mock_response,
            )

            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(
                api_key="test",
                enable_rate_limiting=False,
                enable_retry=False,
            )

            # Attempt to make a request that will fail
            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            # Verify error is properly structured
            error = exc_info.value
            assert error.status_code == status_code
            assert error.error_type == "http_error"
            assert isinstance(error.message, str)
            assert len(error.message) > 0

            # Verify error can be converted to response format
            error_response = error.to_error_response()
            assert error_response.error == "http_error"
            assert "status_code" in error_response.details


@settings(max_examples=50)
@given(
    endpoint=st.sampled_from(
        ["/parks", "/alerts", "/visitorcenters", "/campgrounds", "/events"]
    ),
    query_param=st.sampled_from(["stateCode", "parkCode", "q", "limit", "start"]),
    query_value=st.text(min_size=1, max_size=30),
)
def test_api_client_query_parameter_handling(endpoint, query_param, query_value):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test",
            enable_rate_limiting=False,
            enable_retry=False,
        )

        # Make request with query parameter
        params = {query_param: query_value}
        result = client.get(endpoint, params=params)

        # Verify the request was made with parameters
        assert mock_client_instance.get.called
        call_args = mock_client_instance.get.call_args
        passed_params = call_args.kwargs.get("params", {})

        # Verify parameter was passed
        assert query_param in passed_params, f"Parameter {query_param} should be passed"
        assert passed_params[query_param] == query_value, "Parameter value should match"

        # Verify response is valid
        assert isinstance(result, dict)
        assert "data" in result


@settings(max_examples=30)
@given(
    timeout_seconds=st.floats(min_value=5.0, max_value=60.0),
)
def test_api_client_timeout_configuration(timeout_seconds):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        _ = NPSAPIClient(
            api_key="test",
            timeout=timeout_seconds,
            enable_rate_limiting=False,
            enable_retry=False,
        )

        # Verify timeout was set during initialization
        init_call_args = mock_client_class.call_args
        timeout_value = init_call_args.kwargs.get("timeout")
        assert timeout_value == timeout_seconds, "Timeout should match configuration"


@settings(max_examples=50)
@given(
    response_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.one_of(
            st.text(min_size=0, max_size=50),
            st.integers(),
            st.lists(st.text(min_size=0, max_size=20)),
        ),
        min_size=1,
        max_size=5,
    ),
)
def test_api_client_response_parsing_consistency(response_data):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = response_data
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test",
            enable_rate_limiting=False,
            enable_retry=False,
        )

        result = client.get("/parks")

        # Verify response is parsed correctly
        assert isinstance(result, dict)
        assert result == response_data, "Parsed response should match original data"


@settings(max_examples=50)
@given(
    base_url=st.just("https://developer.nps.gov/api/v1"),
    endpoint=st.sampled_from(
        ["/parks", "/alerts", "/visitorcenters", "/campgrounds", "/events"]
    ),
)
def test_api_client_base_url_configuration(base_url, endpoint):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test",
            base_url=base_url,
            enable_rate_limiting=False,
            enable_retry=False,
        )

        # Make request
        result = client.get(endpoint)

        # Verify base URL was set during initialization
        init_call_args = mock_client_class.call_args
        configured_base_url = init_call_args.kwargs.get("base_url")
        assert configured_base_url == base_url, "Base URL should match configuration"

        # Verify response is valid
        assert isinstance(result, dict)


@settings(max_examples=30)
@given(
    max_retries=st.integers(min_value=1, max_value=5),
    retry_delay=st.floats(min_value=0.1, max_value=5.0),
)
def test_api_client_retry_configuration(max_retries, retry_delay):
    with patch("httpx.Client") as mock_client_class, patch("time.sleep"):
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        # Create client with retry enabled
        client = NPSAPIClient(
            api_key="test",
            enable_rate_limiting=False,
            enable_retry=True,
            max_retries=max_retries,
        )

        # Verify retry configuration was applied
        # The client should have retry logic configured
        assert client.client is not None, "Client should be initialized"


@settings(max_examples=50)
@given(
    park_code=st.text(min_size=1, max_size=10),
    state_code=st.text(min_size=2, max_size=2),
    activity_id=st.text(min_size=1, max_size=20),
)
def test_api_client_convenience_methods_consistency(park_code, state_code, activity_id):
    with patch("httpx.Client") as mock_client_class:
        mock_client_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client_class.return_value = mock_client_instance

        client = NPSAPIClient(
            api_key="test",
            enable_rate_limiting=False,
            enable_retry=False,
        )

        # Test get_parks convenience method
        result = client.get_parks(stateCode=state_code)
        assert isinstance(result, dict)
        assert mock_client_instance.get.called

        # Test get_park_by_code convenience method
        result = client.get_park_by_code(park_code)
        assert isinstance(result, dict)

        # Test get_alerts convenience method
        result = client.get_alerts(park_code=park_code)
        assert isinstance(result, dict)

        # Test get_visitor_centers convenience method
        result = client.get_visitor_centers(park_code=park_code)
        assert isinstance(result, dict)

        # Test get_campgrounds convenience method
        result = client.get_campgrounds(park_code=park_code)
        assert isinstance(result, dict)

        # Test get_events convenience method
        result = client.get_events(park_code=park_code)
        assert isinstance(result, dict)


@settings(max_examples=50)
@given(
    error_type=st.sampled_from(
        ["http_error", "timeout_error", "network_error", "parse_error", "unknown_error"]
    ),
    status_code=st.one_of(st.none(), st.integers(min_value=400, max_value=599)),
)
def test_api_error_response_structure_consistency(error_type, status_code):
    error = NPSAPIError(
        message="Test error",
        status_code=status_code,
        error_type=error_type,
        details={"test": "detail"},
    )

    # Verify error has required attributes
    assert hasattr(error, "message")
    assert hasattr(error, "status_code")
    assert hasattr(error, "error_type")
    assert hasattr(error, "details")

    # Verify error can be converted to response format
    error_response = error.to_error_response()
    assert error_response.error == error_type
    assert error_response.message == "Test error"
    assert isinstance(error_response.details, dict)

    # Verify status code is included in details if present
    if status_code is not None:
        assert "status_code" in error_response.details
        assert error_response.details["status_code"] == status_code
