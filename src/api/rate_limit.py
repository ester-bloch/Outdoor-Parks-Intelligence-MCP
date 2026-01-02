"""Rate limiting utilities for API requests."""

import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API requests.

    This implements a simple token bucket algorithm to limit the rate of API requests.
    """

    def __init__(self, requests_per_hour: int = 1000):
        """
        Initialize the rate limiter.

        Args:
            requests_per_hour: Maximum number of requests allowed per hour
        """
        self.requests_per_hour = requests_per_hour
        self.tokens_per_second = requests_per_hour / 3600.0
        self.max_tokens = requests_per_hour
        self.tokens = float(requests_per_hour)
        self.last_update = time.time()
        self.lock = Lock()

        logger.info(
            f"Initialized rate limiter: {requests_per_hour} requests/hour "
            f"({self.tokens_per_second:.2f} requests/second)"
        )

    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.max_tokens, self.tokens + elapsed * self.tokens_per_second
        )
        self.last_update = now

    def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        Acquire tokens for making a request.

        Args:
            tokens: Number of tokens to acquire (default: 1)
            block: If True, wait until tokens are available. If False, return immediately.

        Returns:
            True if tokens were acquired, False otherwise
        """
        with self.lock:
            self._refill_tokens()

            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(
                    f"Acquired {tokens} token(s). Remaining: {self.tokens:.2f}"
                )
                return True

            if not block:
                logger.debug(
                    f"Failed to acquire {tokens} token(s). Available: {self.tokens:.2f}"
                )
                return False

            # Calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.tokens_per_second

            logger.info(
                f"Rate limit reached. Waiting {wait_time:.2f} seconds for {tokens} token(s)"
            )

        # Release lock while waiting
        time.sleep(wait_time)

        # Try again after waiting
        with self.lock:
            self._refill_tokens()
            if self.tokens >= tokens:
                self.tokens -= tokens
                logger.debug(
                    f"Acquired {tokens} token(s) after waiting. Remaining: {self.tokens:.2f}"
                )
                return True

            # This shouldn't happen, but handle it gracefully
            logger.warning(
                f"Failed to acquire tokens after waiting. Available: {self.tokens:.2f}"
            )
            return False

    def get_available_tokens(self) -> float:
        """
        Get the current number of available tokens.

        Returns:
            Number of available tokens
        """
        with self.lock:
            self._refill_tokens()
            return self.tokens

    def reset(self):
        """Reset the rate limiter to full capacity."""
        with self.lock:
            self.tokens = float(self.max_tokens)
            self.last_update = time.time()
            logger.info("Rate limiter reset to full capacity")
