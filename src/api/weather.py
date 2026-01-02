"""Weather API clients for OpenWeather and Open-Meteo."""

import time
from typing import Any, Dict, Optional

import httpx

from src.api.rate_limit import RateLimiter
from src.api.retry import RetryableHTTPClient, RetryConfig
from src.config import settings
from src.models.errors import ErrorResponse, ErrorType, HTTPStatusCode
from src.utils.logging import get_logger, log_api_request, log_api_response

logger = get_logger(__name__)


class WeatherAPIError(Exception):
    """Custom exception for weather API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_type: str = ErrorType.API_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize weather API error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
            error_type: Type of error
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


class OpenWeatherClient:
    """Client for OpenWeather API."""

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
        Initialize OpenWeather client.

        Args:
            api_key: OpenWeather API key
            base_url: Base URL for OpenWeather API
            timeout: Request timeout in seconds
            enable_rate_limiting: Enable rate limiting
            requests_per_hour: Maximum requests per hour
            enable_retry: Enable retry logic
            max_retries: Maximum number of retries
        """
        self.api_key = api_key or settings.openweather_api_key
        self.base_url = base_url or settings.openweather_api_base_url

        if not self.api_key:
            logger.warning(
                "api_key_missing",
                message="OpenWeather API key not provided. Requests will fail.",
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
        logger.debug("api_client_closed", message="Closed OpenWeather client")

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_details = {"url": str(e.request.url)}
            error_message = f"HTTP {e.response.status_code} error"

            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    error_message = error_data.get("message", error_message)
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

            raise WeatherAPIError(
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
            raise WeatherAPIError(
                message="Failed to parse API response",
                status_code=response.status_code,
                error_type=ErrorType.PARSE_ERROR,
                details={"error": str(e), "response_text": response.text[:500]},
            )

    def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get current weather from OpenWeather."""
        if not self.api_key:
            raise WeatherAPIError(
                message="OpenWeather API key is missing",
                status_code=HTTPStatusCode.UNAUTHORIZED,
                error_type=ErrorType.MISSING_API_KEY,
                details={"provider": "openweather"},
            )

        if self.rate_limiter:
            self.rate_limiter.acquire(tokens=1, block=True)

        endpoint = "weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
        }
        url = f"{self.base_url}/{endpoint}"
        log_api_request(logger, "GET", url, params)

        start_time = time.time()

        try:
            response = self.client.get(endpoint, params=params)
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(logger, "GET", url, response.status_code, duration_ms)
            return self._handle_response(response)
        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = "Request timed out"
            logger.error("api_timeout", url=url, duration_ms=round(duration_ms, 2))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise WeatherAPIError(
                message=error_msg,
                error_type=ErrorType.TIMEOUT_ERROR,
                details={"url": url},
            )
        except httpx.NetworkError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Network error: {str(e)}"
            logger.error("api_network_error", url=url, error=str(e))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise WeatherAPIError(
                message="Network error occurred",
                error_type=ErrorType.NETWORK_ERROR,
                details={"url": url, "error": str(e)},
            )
        except WeatherAPIError:
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("api_unexpected_error", url=url, error=str(e), exc_info=True)
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise WeatherAPIError(
                message="Unexpected error occurred",
                error_type=ErrorType.UNKNOWN_ERROR,
                details={"error": str(e), "url": url},
            )


class OpenMeteoClient:
    """Client for Open-Meteo API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 20.0,
        enable_rate_limiting: bool = True,
        requests_per_hour: int = 1000,
        enable_retry: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize Open-Meteo client.

        Args:
            base_url: Base URL for Open-Meteo API
            timeout: Request timeout in seconds
            enable_rate_limiting: Enable rate limiting
            requests_per_hour: Maximum requests per hour
            enable_retry: Enable retry logic
            max_retries: Maximum number of retries
        """
        self.base_url = base_url or settings.open_meteo_api_base_url

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
        logger.debug("api_client_closed", message="Closed Open-Meteo client")

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_details = {"url": str(e.request.url)}
            error_message = f"HTTP {e.response.status_code} error"

            try:
                error_data = e.response.json()
                if isinstance(error_data, dict):
                    error_message = error_data.get("reason", error_message)
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

            raise WeatherAPIError(
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
            raise WeatherAPIError(
                message="Failed to parse API response",
                status_code=response.status_code,
                error_type=ErrorType.PARSE_ERROR,
                details={"error": str(e), "response_text": response.text[:500]},
            )

    def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get current weather from Open-Meteo."""
        if self.rate_limiter:
            self.rate_limiter.acquire(tokens=1, block=True)

        endpoint = "forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "windspeed_unit": "ms",
        }
        url = f"{self.base_url}/{endpoint}"
        log_api_request(logger, "GET", url, params)

        start_time = time.time()

        try:
            response = self.client.get(endpoint, params=params)
            duration_ms = (time.time() - start_time) * 1000
            log_api_response(logger, "GET", url, response.status_code, duration_ms)
            return self._handle_response(response)
        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = "Request timed out"
            logger.error("api_timeout", url=url, duration_ms=round(duration_ms, 2))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise WeatherAPIError(
                message=error_msg,
                error_type=ErrorType.TIMEOUT_ERROR,
                details={"url": url},
            )
        except httpx.NetworkError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Network error: {str(e)}"
            logger.error("api_network_error", url=url, error=str(e))
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise WeatherAPIError(
                message="Network error occurred",
                error_type=ErrorType.NETWORK_ERROR,
                details={"url": url, "error": str(e)},
            )
        except WeatherAPIError:
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("api_unexpected_error", url=url, error=str(e), exc_info=True)
            log_api_response(logger, "GET", url, 0, duration_ms, error=error_msg)
            raise WeatherAPIError(
                message="Unexpected error occurred",
                error_type=ErrorType.UNKNOWN_ERROR,
                details={"error": str(e), "url": url},
            )


_openweather_client: Optional[OpenWeatherClient] = None
_open_meteo_client: Optional[OpenMeteoClient] = None


def get_openweather_client() -> OpenWeatherClient:
    """Get or create the global OpenWeather client instance."""
    global _openweather_client
    if _openweather_client is None:
        _openweather_client = OpenWeatherClient()
    return _openweather_client


def get_open_meteo_client() -> OpenMeteoClient:
    """Get or create the global Open-Meteo client instance."""
    global _open_meteo_client
    if _open_meteo_client is None:
        _open_meteo_client = OpenMeteoClient()
    return _open_meteo_client


def close_weather_clients() -> None:
    """Close global weather client instances."""
    global _openweather_client, _open_meteo_client
    if _openweather_client is not None:
        _openweather_client.close()
        _openweather_client = None
    if _open_meteo_client is not None:
        _open_meteo_client.close()
        _open_meteo_client = None
