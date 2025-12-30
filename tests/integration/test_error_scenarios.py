"""Integration tests for error scenarios.

Tests API failures, validation errors, and network issues.
Verifies graceful degradation and error recovery.
Requirements: 1.4, 3.4
"""

from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest
from pydantic import ValidationError

from src.api.client import NPSAPIClient, NPSAPIError
from src.handlers.find_parks import find_parks
from src.handlers.get_alerts import get_alerts
from src.handlers.get_campgrounds import get_campgrounds
from src.handlers.get_events import get_events
from src.handlers.get_park_details import get_park_details
from src.handlers.get_visitor_centers import get_visitor_centers
from src.models.errors import ErrorResponse, ErrorType
from src.models.requests import (
    FindParksRequest,
    GetAlertsRequest,
    GetCampgroundsRequest,
    GetEventsRequest,
    GetParkDetailsRequest,
    GetVisitorCentersRequest,
)


class TestAPIFailureScenarios:
    """Test API failure scenarios and error handling."""

    def test_api_500_error_handling(self):
        """Test handling of API 500 Internal Server Error."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.json.return_value = {"message": "Internal Server Error"}

            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="HTTP 500",
                request=Mock(url="https://test.com/api"),
                response=mock_response,
            )
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.status_code == 500
            assert error.error_type == "http_error"
            assert "500" in error.message or "Internal" in error.message

    def test_api_503_service_unavailable(self):
        """Test handling of API 503 Service Unavailable."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.text = "Service Unavailable"
            mock_response.json.return_value = {"message": "Service Unavailable"}

            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="HTTP 503",
                request=Mock(url="https://test.com/api"),
                response=mock_response,
            )
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.status_code == 503
            assert error.error_type == "http_error"

    def test_api_429_rate_limit_exceeded(self):
        """Test handling of API 429 Rate Limit Exceeded."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Too Many Requests"
            mock_response.json.return_value = {"message": "Rate limit exceeded"}
            mock_response.headers = {"Retry-After": "60"}

            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="HTTP 429",
                request=Mock(url="https://test.com/api"),
                response=mock_response,
            )
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.status_code == 429
            assert error.error_type == "http_error"

    def test_api_401_unauthorized(self):
        """Test handling of API 401 Unauthorized."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.json.return_value = {"message": "Invalid API key"}

            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="HTTP 401",
                request=Mock(url="https://test.com/api"),
                response=mock_response,
            )
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.status_code == 401
            assert error.error_type == "http_error"

    def test_api_404_not_found(self):
        """Test handling of API 404 Not Found."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.json.return_value = {"message": "Park not found"}

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

    def test_api_400_bad_request(self):
        """Test handling of API 400 Bad Request."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            mock_response.json.return_value = {"message": "Invalid parameters"}

            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                message="HTTP 400",
                request=Mock(url="https://test.com/api"),
                response=mock_response,
            )
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.status_code == 400
            assert error.error_type == "http_error"


class TestNetworkFailureScenarios:
    """Test network failure scenarios and error handling."""

    def test_network_connection_error(self):
        """Test handling of network connection errors."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.NetworkError(
                "Failed to establish connection"
            )
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "network_error"
            assert "network" in error.message.lower()

    def test_request_timeout_error(self):
        """Test handling of request timeout errors."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.TimeoutException(
                "Request timed out after 30 seconds"
            )
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "timeout_error"
            assert (
                "timeout" in error.message.lower()
                or "timed out" in error.message.lower()
            )

    def test_connection_timeout_error(self):
        """Test handling of connection timeout errors."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.ConnectTimeout(
                "Connection timeout"
            )
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "timeout_error"

    def test_read_timeout_error(self):
        """Test handling of read timeout errors."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.ReadTimeout("Read timeout")
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "timeout_error"

    def test_dns_resolution_error(self):
        """Test handling of DNS resolution errors."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_client_instance.get.side_effect = httpx.NetworkError(
                "Failed to resolve hostname"
            )
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "network_error"


class TestValidationErrorScenarios:
    """Test validation error scenarios and error handling."""

    def test_invalid_state_code_validation(self):
        """Test validation of invalid state codes."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            request = FindParksRequest(state_code="XX")  # Invalid state code
            result = find_parks(request)

            assert "Invalid state code" in result.get("error", "")
            assert "validStateCodes" in result
            assert isinstance(result.get("validStateCodes"), list)

    def test_invalid_limit_parameter(self):
        """Test validation of invalid limit parameter."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Limit exceeding maximum should raise validation error
            with pytest.raises(ValidationError):
                FindParksRequest(limit=100)  # Max is 50

    def test_missing_required_field_validation(self):
        """Test validation of missing required fields."""
        # GetParkDetailsRequest requires park_code
        with pytest.raises(ValidationError):
            GetParkDetailsRequest()  # Missing required park_code

    def test_invalid_field_type_validation(self):
        """Test validation of invalid field types."""
        with pytest.raises(ValidationError):
            FindParksRequest(limit="not_a_number")  # limit should be int

    def test_empty_string_validation(self):
        """Test validation of empty strings."""
        with pytest.raises(ValidationError):
            GetParkDetailsRequest(park_code="")  # Empty string not allowed


class TestGracefulDegradationScenarios:
    """Test graceful degradation and error recovery."""

    def test_handler_graceful_degradation_on_api_error(self):
        """Test that handlers gracefully degrade on API errors."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Simulate API error
            mock_client.get_parks.side_effect = NPSAPIError(
                message="API service unavailable",
                status_code=503,
                error_type="http_error",
            )

            request = FindParksRequest()

            with pytest.raises(NPSAPIError):
                find_parks(request)

    def test_get_park_details_api_error_handling(self):
        """Test get_park_details error handling."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.get_park_by_code.side_effect = NPSAPIError(
                message="Park not found",
                status_code=404,
                error_type="http_error",
            )

            request = GetParkDetailsRequest(park_code="invalid")

            with pytest.raises(NPSAPIError):
                get_park_details(request)

    def test_get_alerts_api_error_handling(self):
        """Test get_alerts error handling."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.get_alerts.side_effect = NPSAPIError(
                message="API error",
                status_code=500,
                error_type="http_error",
            )

            request = GetAlertsRequest(park_code="yose")

            with pytest.raises(NPSAPIError):
                get_alerts(request)

    def test_get_visitor_centers_api_error_handling(self):
        """Test get_visitor_centers error handling."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.get_visitor_centers.side_effect = NPSAPIError(
                message="API error",
                status_code=500,
                error_type="http_error",
            )

            request = GetVisitorCentersRequest(park_code="yose")

            with pytest.raises(NPSAPIError):
                get_visitor_centers(request)

    def test_get_campgrounds_api_error_handling(self):
        """Test get_campgrounds error handling."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.get_campgrounds.side_effect = NPSAPIError(
                message="API error",
                status_code=500,
                error_type="http_error",
            )

            request = GetCampgroundsRequest(park_code="yose")

            with pytest.raises(NPSAPIError):
                get_campgrounds(request)

    def test_get_events_api_error_handling(self):
        """Test get_events error handling."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.get_events.side_effect = NPSAPIError(
                message="API error",
                status_code=500,
                error_type="http_error",
            )

            request = GetEventsRequest(park_code="yose")

            with pytest.raises(NPSAPIError):
                get_events(request)


class TestErrorRecoveryScenarios:
    """Test error recovery and retry scenarios."""

    def test_retry_on_transient_error_recovery(self):
        """Test recovery from transient errors with retry."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()

            # First call fails with 503, second succeeds
            mock_response_fail = Mock()
            mock_response_fail.status_code = 503
            mock_response_fail.text = "Service unavailable"
            mock_response_fail.json.return_value = {"message": "Service unavailable"}

            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"data": []}
            mock_response_success.raise_for_status = Mock()

            call_count = [0]

            def get_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise httpx.HTTPStatusError(
                        message="Service unavailable",
                        request=Mock(url="https://test.com/api"),
                        response=mock_response_fail,
                    )
                else:
                    return mock_response_success

            mock_client_instance.get.side_effect = get_side_effect
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(
                enable_rate_limiting=False, enable_retry=True, max_retries=2
            )

            result = client.get("/parks")
            assert result == {"data": []}
            assert call_count[0] == 2

    def test_retry_exhaustion_on_persistent_error(self):
        """Test that retries are exhausted on persistent errors."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_response.json.return_value = {"message": "Service unavailable"}

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

    def test_error_response_conversion(self):
        """Test conversion of NPSAPIError to ErrorResponse."""
        error = NPSAPIError(
            message="API error occurred",
            status_code=500,
            error_type="http_error",
            details={"endpoint": "/parks", "method": "GET"},
        )

        error_response = error.to_error_response()

        assert isinstance(error_response, ErrorResponse)
        assert error_response.error == "http_error"
        assert error_response.message == "API error occurred"
        assert error_response.details["status_code"] == 500
        assert error_response.details["endpoint"] == "/parks"


class TestConcurrentErrorScenarios:
    """Test error handling in concurrent scenarios."""

    def test_multiple_handlers_with_api_errors(self):
        """Test multiple handlers handling API errors concurrently."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Simulate API error for all handlers
            api_error = NPSAPIError(
                message="API service unavailable",
                status_code=503,
                error_type="http_error",
            )

            mock_client.get_parks.side_effect = api_error
            mock_client.get_park_by_code.side_effect = api_error
            mock_client.get_alerts.side_effect = api_error
            mock_client.get_visitor_centers.side_effect = api_error
            mock_client.get_campgrounds.side_effect = api_error
            mock_client.get_events.side_effect = api_error

            # All handlers should raise the same error
            with pytest.raises(NPSAPIError):
                find_parks(FindParksRequest())

            with pytest.raises(NPSAPIError):
                get_park_details(GetParkDetailsRequest(park_code="yose"))

            with pytest.raises(NPSAPIError):
                get_alerts(GetAlertsRequest(park_code="yose"))

            with pytest.raises(NPSAPIError):
                get_visitor_centers(GetVisitorCentersRequest(park_code="yose"))

            with pytest.raises(NPSAPIError):
                get_campgrounds(GetCampgroundsRequest(park_code="yose"))

            with pytest.raises(NPSAPIError):
                get_events(GetEventsRequest(park_code="yose"))


class TestPartialFailureScenarios:
    """Test handling of partial failures and degraded responses."""

    def test_empty_response_handling(self):
        """Test handling of empty API responses."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            mock_client.get_parks.return_value = {
                "total": "0",
                "limit": "50",
                "start": "0",
                "data": [],
            }

            with patch("src.handlers.find_parks.get_client", return_value=mock_client):
                request = FindParksRequest()
                result = find_parks(request)

                assert result.get("total") == 0
                assert result.get("parks") == []

    def test_malformed_response_handling(self):
        """Test handling of malformed API responses."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_instance = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.text = "Invalid JSON"
            mock_response.raise_for_status = Mock()
            mock_client_instance.get.return_value = mock_response
            mock_client_class.return_value = mock_client_instance

            client = NPSAPIClient(enable_rate_limiting=False, enable_retry=False)

            with pytest.raises(NPSAPIError) as exc_info:
                client.get("/parks")

            error = exc_info.value
            assert error.error_type == "parse_error"

    def test_partial_data_response_handling(self):
        """Test handling of responses with missing optional fields."""
        with patch("src.api.client.get_client") as mock_get_client:
            mock_client = Mock()
            mock_get_client.return_value = mock_client

            # Response with minimal data
            mock_client.get_parks.return_value = {
                "total": "1",
                "limit": "50",
                "start": "0",
                "data": [
                    {
                        "id": "test-id",
                        "parkCode": "yose",
                        "fullName": "Yosemite",
                        "name": "Yosemite",
                        "url": "https://example.com",
                        "description": "Test",
                        "latitude": "0",
                        "longitude": "0",
                        "latLong": "lat:0, long:0",
                        "states": "CA",
                        "contacts": {},
                        "entranceFees": [],
                        "entrancePasses": [],
                        "fees": [],
                        "directionsInfo": "",
                        "directionsUrl": "",
                        "operatingHours": [],
                        "addresses": [],
                        "images": [],
                        "weatherInfo": "",
                        "designation": "National Park",
                    }
                ],
            }

            with patch("src.handlers.find_parks.get_client", return_value=mock_client):
                request = FindParksRequest()
                result = find_parks(request)

                assert result.get("total") == 1
                assert len(result.get("parks", [])) == 1
