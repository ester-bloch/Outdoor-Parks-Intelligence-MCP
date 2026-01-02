"""Retry logic with exponential backoff for API requests."""

import logging
import time
from functools import wraps
from typing import Callable, Optional, Tuple, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retry_on_status_codes: Optional[Tuple[int, ...]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            retry_on_status_codes: HTTP status codes that should trigger a retry
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_on_status_codes = retry_on_status_codes or (
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        )


def calculate_backoff_delay(
    attempt: int, initial_delay: float, max_delay: float, exponential_base: float
) -> float:
    """
    Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation

    Returns:
        Delay in seconds
    """
    delay = initial_delay * (exponential_base**attempt)
    return min(delay, max_delay)


def should_retry_error(
    error: Exception, retry_on_status_codes: Tuple[int, ...]
) -> bool:
    """
    Determine if an error should trigger a retry.

    Args:
        error: The exception that occurred
        retry_on_status_codes: Status codes that should trigger a retry

    Returns:
        True if the error should trigger a retry
    """
    # Retry on network errors
    if isinstance(error, (httpx.NetworkError, httpx.TimeoutException)):
        return True

    # Retry on specific HTTP status codes
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in retry_on_status_codes

    return False


def retry_with_backoff(config: Optional[RetryConfig] = None):
    """
    Add retry logic with exponential backoff to a function.

    Args:
        config: Retry configuration. If None, uses default configuration.

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for {func.__name__}"
                        )
                        break

                    if not should_retry_error(e, config.retry_on_status_codes):
                        logger.debug(
                            f"Error not retryable for {func.__name__}: {type(e).__name__}"
                        )
                        break

                    # Calculate backoff delay
                    delay = calculate_backoff_delay(
                        attempt,
                        config.initial_delay,
                        config.max_delay,
                        config.exponential_base,
                    )

                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_retries + 1} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f} seconds. Error: {e}"
                    )

                    time.sleep(delay)

            # If we get here, all retries failed
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class RetryableHTTPClient:
    """
    HTTP client wrapper with built-in retry logic.

    This wraps an HTTPX client and adds retry logic to all requests.
    """

    def __init__(self, client: httpx.Client, config: Optional[RetryConfig] = None):
        """
        Initialize the retryable HTTP client.

        Args:
            client: HTTPX client to wrap
            config: Retry configuration
        """
        self.client = client
        self.config = config or RetryConfig()

    def get(self, *args, **kwargs) -> httpx.Response:
        """Make a GET request with retry logic."""

        @retry_with_backoff(self.config)
        def _get():
            return self.client.get(*args, **kwargs)

        return _get()

    def post(self, *args, **kwargs) -> httpx.Response:
        """Make a POST request with retry logic."""

        @retry_with_backoff(self.config)
        def _post():
            return self.client.post(*args, **kwargs)

        return _post()

    def put(self, *args, **kwargs) -> httpx.Response:
        """Make a PUT request with retry logic."""

        @retry_with_backoff(self.config)
        def _put():
            return self.client.put(*args, **kwargs)

        return _put()

    def delete(self, *args, **kwargs) -> httpx.Response:
        """Make a DELETE request with retry logic."""

        @retry_with_backoff(self.config)
        def _delete():
            return self.client.delete(*args, **kwargs)

        return _delete()
