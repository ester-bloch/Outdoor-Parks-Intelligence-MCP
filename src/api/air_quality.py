"""Air quality API client using AirVisual."""

import time
from typing import Any, Dict, Optional

import httpx

from src.api.rate_limit import RateLimiter
from src.api.retry import RetryableHTTPClient, RetryConfig
from src.config import settings
from src.models.errors import ErrorResponse, ErrorType, HTTPStatusCode
from src.utils.logging import get_logger, log_api_request, log_api_response

logger = get_logger(__name__)


class AirQualityAPIError(Exception):
    """Custom exception for AirVisual API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_type: str = ErrorType.API_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize AirQualityAPIError.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
            error_type: Type of error from ErrorType enum
            details: Additional error details
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


class AirQualityClient:
    """Client for interacting with the AirVisual API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 20.0,
        enable_rate_limiting: bool = True,
        requests_per_hour: int = 1000,
        enable_retry: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize AirQualityClient.

        Args:
            api_key: AirVisual API key (defaults to settings)
            base_url: Base URL for AirVisual API (defaults to settings)
            timeout: Request timeout in seconds
            enable_rate_limiting: Whether to enable rate limiting
            requests_per_hour: Maximum requests per hour for rate limiting
            enable_retry: Whether to enable retry logic
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key or settings.airvisual_api_key
        self.base_url = base_url or settings.airvisual_api_base_url

        if not self.api_key:
            logger.warning(
                "api_key_missing",
                message="AirVisual API key not provided. Requests will fail.",
            )

        base_client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            follow_redirects=True,
        )

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

        self.rate_limiter: Optional[RateLimiter] = None
        if enable_rate_limiting:
            self.rate_limiter = RateLimiter(requests_per_hour=requests_per_hour)
            logger.info(
                "rate_limiting_enabled",
                requests_per_hour=requests_per_hour,
                message="Enabled rate limiting",
            )

        logger.info("api_client_initialized", base_url=self.base_url)

    def close(self) -> None:
        """Close the HTTP client."""
        if isinstance(self.client, RetryableHTTPClient):
            self.client.client.close()
        else:
            self.client.close()
        logger.debug("api_client_closed", message="Closed AirVisual API client")

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_details = {"url": str(e.request.url)}
            error_message = f"HTTP {e.response.status_code} error"

            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    error_message = error_data.get("data", {}).get(
                        "message", error_message
                    )
                    error_details.update(error_data)
            except Exception:
                error_details["response_text"] = e.response.text[:500]

            logger.error(
                "api_request_failed",
                error=error_message,
                status_code=e.response.status_code,
                url=str(e.request.url),
                details=error_details,
            )

            raise AirQualityAPIError(
                message=error_message,
                status_code=e.response.status_code,
                error_type=ErrorType.HTTP_ERROR,
                details=error_details,
            )

        try:
            data = response.json()
            logger.debug("response_parsed", url=str(response.url))
            return data
        except Exception as e:
            logger.error("response_parse_failed", error=str(e), url=str(response.url))
            raise AirQualityAPIError(
                message="Failed to parse API response",
                status_code=response.status_code,
                error_type=ErrorType.PARSE_ERROR,
                details={"error": str(e), "response_text": response.text[:500]},
            )

    def get_nearest_city(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get air quality for the nearest city to a coordinate."""
        if not self.api_key:
            raise AirQualityAPIError(
                message="AirVisual API key is missing",
                status_code=HTTPStatusCode.UNAUTHORIZED,
                error_type=ErrorType.MISSING_API_KEY,
                details={"provider": "airvisual"},
            )

        if self.rate_limiter:
            self.rate_limiter.acquire(tokens=1, block=True)

        endpoint = "nearest_city"
        params = {"lat": latitude, "lon": longitude, "key": self.api_key}
        url = f"{self.base_url}/{endpoint}"
        log_api_request(logger, "GET", url, params)

        start_time = time.time()

        try:
            response = self.client.get(endpoint, params=params)
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(logger, "GET", url, response.status_code, duration_ms)

            data = self._handle_response(response)
            if data.get("status") != "success":
                raise AirQualityAPIError(
                    message=data.get("data", {}).get("message", "AirVisual error"),
                    status_code=response.status_code,
                    error_type=ErrorType.API_ERROR,
                    details={"provider": "airvisual", "response": data},
                )
            return data
        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = "Request timed out"
            logger.error("api_timeout", url=url, duration_ms=round(duration_ms, 2))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise AirQualityAPIError(
                message=error_msg,
                error_type=ErrorType.TIMEOUT_ERROR,
                details={"url": url},
            )
        except httpx.NetworkError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Network error: {str(e)}"
            logger.error("api_network_error", url=url, error=str(e))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise AirQualityAPIError(
                message="Network error occurred",
                error_type=ErrorType.NETWORK_ERROR,
                details={"url": url, "error": str(e)},
            )
        except AirQualityAPIError:
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("api_unexpected_error", url=url, error=str(e), exc_info=True)
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise AirQualityAPIError(
                message="Unexpected error occurred",
                error_type=ErrorType.UNKNOWN_ERROR,
                details={"error": str(e), "url": url},
            )


_client: Optional[AirQualityClient] = None


def get_air_quality_client() -> AirQualityClient:
    """Get or create the global AirVisual client instance."""
    global _client
    if _client is None:
        _client = AirQualityClient()
    return _client


def close_air_quality_client() -> None:
    """Close the global AirVisual client instance."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
