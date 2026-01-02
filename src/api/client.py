"""NPS API client using HTTPX."""

import time
from typing import Any, Dict, Optional, TypeVar

import httpx
from pydantic import BaseModel

from src.api.rate_limit import RateLimiter
from src.api.retry import RetryableHTTPClient, RetryConfig
from src.config import settings
from src.models.errors import ErrorResponse
from src.utils.logging import get_logger, log_api_request, log_api_response

# Set up structured logger
logger = get_logger(__name__)

# Generic type for response data
T = TypeVar("T", bound=BaseModel)


class NPSAPIError(Exception):
    """Custom exception for NPS API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_type: str = "api_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the NPSAPIError exception.

        Args:
            message: A human-readable error message.
            status_code: The HTTP status code returned by the API.
            error_type: The category of the error.
            details: Additional dictionary containing error specifics.
        """
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

    def to_error_response(self) -> ErrorResponse:
        """Convert to ErrorResponse model."""
        details = self.details.copy()
        if self.status_code:
            details["status_code"] = self.status_code
        return ErrorResponse(
            error=self.error_type, message=self.message, details=details
        )


class _UseSettingsType:
    """Sentinel type for using settings-based API key."""


_USE_SETTINGS = _UseSettingsType()


class NPSAPIClient:
    """Client for interacting with the National Park Service API."""

    def __init__(
        self,
        api_key: Optional[str] | _UseSettingsType = _USE_SETTINGS,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        enable_rate_limiting: bool = True,
        requests_per_hour: int = 1000,
        enable_retry: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize the NPS API client.

        Args:
            api_key: NPS API key. If not provided, uses settings.nps_api_key
            base_url: Base URL for the NPS API. If not provided, uses settings.nps_api_base_url
            timeout: Request timeout in seconds
            enable_rate_limiting: Whether to enable rate limiting
            requests_per_hour: Maximum requests per hour (default: 1000)
            enable_retry: Whether to enable automatic retries
            max_retries: Maximum number of retry attempts
        """
        if api_key is _USE_SETTINGS:
            self.api_key = settings.nps_api_key
        else:
            self.api_key = api_key
        self.base_url = base_url or settings.nps_api_base_url

        if not self.api_key:
            logger.warning(
                "api_key_missing",
                message="NPS API key not provided. API requests will fail without authentication.",
            )

        # Create HTTPX client with authentication headers
        headers = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        base_client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

        # Wrap with retry logic if enabled
        if enable_retry:
            retry_config = RetryConfig(
                max_retries=max_retries,
                initial_delay=1.0,
                max_delay=60.0,
                exponential_base=2.0,
            )
            self.client = RetryableHTTPClient(base_client, retry_config)
            logger.info(
                "retry_enabled",
                max_retries=max_retries,
                message="Enabled retry logic",
            )
        else:
            self.client = base_client

        # Initialize rate limiter if enabled
        self.rate_limiter: Optional[RateLimiter] = None
        if enable_rate_limiting:
            self.rate_limiter = RateLimiter(requests_per_hour=requests_per_hour)
            logger.info(
                "rate_limiting_enabled",
                requests_per_hour=requests_per_hour,
                message="Enabled rate limiting",
            )

        logger.info("api_client_initialized", base_url=self.base_url)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        # Handle both wrapped and unwrapped clients
        if isinstance(self.client, RetryableHTTPClient):
            self.client.client.close()
        else:
            self.client.close()
        logger.debug("api_client_closed", message="Closed NPS API client")

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response and extract JSON data.

        Args:
            response: HTTPX response object

        Returns:
            Parsed JSON response data

        Raises:
            NPSAPIError: If the response indicates an error
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_message = f"HTTP {e.response.status_code} error"
            error_details = {"url": str(e.request.url)}

            # Try to extract error details from response
            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    error_message = error_data.get("message", error_message)
                    error_details.update(error_data)
            except Exception:
                # If we can't parse JSON, use the response text
                error_details["response_text"] = e.response.text[:500]

            logger.error(
                "api_request_failed",
                error=error_message,
                status_code=e.response.status_code,
                url=str(e.request.url),
                details=error_details,
            )

            raise NPSAPIError(
                message=error_message,
                status_code=e.response.status_code,
                error_type="http_error",
                details=error_details,
            )

        # Parse JSON response
        try:
            data = response.json()
            logger.debug("response_parsed", url=str(response.url))
            return data
        except Exception as e:
            logger.error("response_parse_failed", error=str(e), url=str(response.url))
            raise NPSAPIError(
                message="Failed to parse API response",
                status_code=response.status_code,
                error_type="parse_error",
                details={"error": str(e), "response_text": response.text[:500]},
            )

    def _build_url(self, endpoint: str) -> str:
        """
        Build a normalized endpoint path with a leading slash.

        Args:
            endpoint: API endpoint path (e.g., "/parks" or "parks")

        Returns:
            Normalized endpoint path with a leading slash
        """
        return f"/{endpoint.lstrip('/')}"

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the NPS API.

        Args:
            endpoint: API endpoint path (e.g., "/parks")
            params: Query parameters

        Returns:
            Parsed JSON response data

        Raises:
            NPSAPIError: If the request fails
        """
        # Acquire rate limit token if rate limiting is enabled
        if self.rate_limiter:
            self.rate_limiter.acquire(tokens=1, block=True)

        path = self._build_url(endpoint)
        url = self.base_url + path
        # Log the outgoing request
        log_api_request(logger, "GET", url, params)

        # Track request timing
        start_time = time.time()
        status_code = None
        error_msg = None

        try:
            response = self.client.get(path, params=params)
            status_code = response.status_code
            duration_ms = (time.time() - start_time) * 1000

            # Log the response
            log_api_response(logger, "GET", url, status_code, duration_ms)

            return self._handle_response(response)
        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = "Request timed out"

            logger.error("api_timeout", url=url, duration_ms=round(duration_ms, 2))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)

            raise NPSAPIError(
                message=error_msg,
                error_type="timeout_error",
                details={"url": url},
            )
        except httpx.NetworkError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Network error: {str(e)}"

            logger.error("api_network_error", url=url, error=str(e))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)

            raise NPSAPIError(
                message="Network error occurred",
                error_type="network_error",
                details={"url": url, "error": str(e)},
            )
        except NPSAPIError:
            # Re-raise our custom errors (already logged in _handle_response)
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"

            logger.error("api_unexpected_error", url=url, error=str(e), exc_info=True)
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)

            raise NPSAPIError(
                message="Unexpected error occurred",
                error_type="unknown_error",
                details={"error": str(e), "url": url},
            )

    def get_parks(self, **params) -> Dict[str, Any]:
        """
        Get parks from the NPS API.

        Args:
            **params: Query parameters (stateCode, q, limit, start, etc.)

        Returns:
            NPS API response with park data
        """
        return self.get("/parks", params=params)

    def get_park_by_code(self, park_code: str) -> Dict[str, Any]:
        """
        Get a specific park by its park code.

        Args:
            park_code: Four-letter park code

        Returns:
            NPS API response with park data
        """
        return self.get("/parks", params={"parkCode": park_code})

    def get_alerts(self, park_code: Optional[str] = None, **params) -> Dict[str, Any]:
        """
        Get alerts from the NPS API.

        Args:
            park_code: Optional park code to filter alerts
            **params: Additional query parameters

        Returns:
            NPS API response with alert data
        """
        if park_code:
            params["parkCode"] = park_code
        return self.get("/alerts", params=params)

    def get_visitor_centers(
        self, park_code: Optional[str] = None, **params
    ) -> Dict[str, Any]:
        """
        Get visitor centers from the NPS API.

        Args:
            park_code: Optional park code to filter visitor centers
            **params: Additional query parameters

        Returns:
            NPS API response with visitor center data
        """
        if park_code:
            params["parkCode"] = park_code
        return self.get("/visitorcenters", params=params)

    def get_campgrounds(
        self, park_code: Optional[str] = None, **params
    ) -> Dict[str, Any]:
        """
        Get campgrounds from the NPS API.

        Args:
            park_code: Optional park code to filter campgrounds
            **params: Additional query parameters

        Returns:
            NPS API response with campground data
        """
        if park_code:
            params["parkCode"] = park_code
        return self.get("/campgrounds", params=params)

    def get_events(self, park_code: Optional[str] = None, **params) -> Dict[str, Any]:
        """
        Get events from the NPS API.

        Args:
            park_code: Optional park code to filter events
            **params: Additional query parameters

        Returns:
            NPS API response with event data
        """
        if park_code:
            params["parkCode"] = park_code
        return self.get("/events", params=params)


# Global client instance
_client: Optional[NPSAPIClient] = None


def get_client() -> NPSAPIClient:
    """
    Get or create the global NPS API client instance.

    Returns:
        NPSAPIClient instance
    """
    global _client
    if _client is None:
        _client = NPSAPIClient()
    return _client


def close_client():
    """Close the global client instance."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
