"""Unit tests for structured logging."""

import logging
from io import StringIO

import pytest
import structlog

from src.utils.logging import (
    censor_sensitive_data,
    configure_logging,
    get_logger,
    log_api_request,
    log_api_response,
    log_request,
    log_response,
)


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_configure_logging_info_level(self):
        """Test configuring logging at INFO level."""
        configure_logging(log_level="INFO", json_logs=False)
        logger = get_logger(__name__)
        assert logger is not None
        # Logger can be either BoundLogger or BoundLoggerLazyProxy
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_configure_logging_debug_level(self):
        """Test configuring logging at DEBUG level."""
        configure_logging(log_level="DEBUG", json_logs=False)
        logger = get_logger(__name__)
        assert logger is not None

    def test_configure_logging_json_format(self):
        """Test configuring logging with JSON output."""
        configure_logging(log_level="INFO", json_logs=True)
        logger = get_logger(__name__)
        assert logger is not None

    def test_configure_logging_without_timestamp(self):
        """Test configuring logging without timestamps."""
        configure_logging(log_level="INFO", json_logs=False, include_timestamp=False)
        logger = get_logger(__name__)
        assert logger is not None


class TestLoggerCreation:
    """Test logger creation."""

    def test_get_logger_with_name(self):
        """Test getting a logger with a specific name."""
        logger = get_logger("test_module")
        assert logger is not None
        # Logger can be either BoundLogger or BoundLoggerLazyProxy
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_get_logger_without_name(self):
        """Test getting a logger without a name."""
        logger = get_logger()
        assert logger is not None


class TestRequestResponseLogging:
    """Test request/response logging helpers."""

    def test_log_request(self, caplog):
        """Test logging a tool request."""
        configure_logging(log_level="INFO", json_logs=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            log_request(logger, "findParks", {"stateCode": "CA", "limit": 10})

        # Check that the log was created
        assert len(caplog.records) > 0

    def test_log_response_success(self, caplog):
        """Test logging a successful response."""
        configure_logging(log_level="INFO", json_logs=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            log_response(logger, "findParks", success=True, response_size=5)

        assert len(caplog.records) > 0

    def test_log_response_failure(self, caplog):
        """Test logging a failed response."""
        configure_logging(log_level="INFO", json_logs=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.WARNING):
            log_response(logger, "findParks", success=False, error="API error")

        assert len(caplog.records) > 0


class TestAPILogging:
    """Test API request/response logging helpers."""

    def test_log_api_request(self, caplog):
        """Test logging an API request."""
        configure_logging(log_level="DEBUG", json_logs=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.DEBUG):
            log_api_request(
                logger, "GET", "https://api.example.com/parks", {"limit": 10}
            )

        assert len(caplog.records) > 0

    def test_log_api_response_success(self, caplog):
        """Test logging a successful API response."""
        configure_logging(log_level="DEBUG", json_logs=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.DEBUG):
            log_api_response(
                logger, "GET", "https://api.example.com/parks", 200, duration_ms=150.5
            )

        assert len(caplog.records) > 0

    def test_log_api_response_error(self, caplog):
        """Test logging an API error response."""
        configure_logging(log_level="ERROR", json_logs=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.ERROR):
            log_api_response(
                logger,
                "GET",
                "https://api.example.com/parks",
                500,
                duration_ms=100.0,
                error="Internal server error",
            )

        assert len(caplog.records) > 0

    def test_log_api_response_client_error(self, caplog):
        """Test logging a client error response."""
        configure_logging(log_level="WARNING", json_logs=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.WARNING):
            log_api_response(
                logger, "GET", "https://api.example.com/parks", 404, duration_ms=50.0
            )

        assert len(caplog.records) > 0


class TestSensitiveDataCensoring:
    """Test sensitive data censoring."""

    def test_censor_api_key(self):
        """Test that API keys are censored."""
        event_dict = {
            "message": "Making request",
            "api_key": "secret_key_12345",
            "other_data": "visible",
        }

        result = censor_sensitive_data(None, "info", event_dict)

        assert result["api_key"] == "***REDACTED***"
        assert result["other_data"] == "visible"

    def test_censor_authorization_header(self):
        """Test that authorization headers are censored."""
        event_dict = {
            "message": "Making request",
            "authorization": "Bearer token123",
            "url": "https://api.example.com",
        }

        result = censor_sensitive_data(None, "info", event_dict)

        assert result["authorization"] == "***REDACTED***"
        assert result["url"] == "https://api.example.com"

    def test_censor_nested_sensitive_data(self):
        """Test that nested sensitive data is censored."""
        event_dict = {
            "message": "Making request",
            "headers": {"X-Api-Key": "secret123", "Content-Type": "application/json"},
            "url": "https://api.example.com",
        }

        result = censor_sensitive_data(None, "info", event_dict)

        assert result["headers"]["X-Api-Key"] == "***REDACTED***"
        assert result["headers"]["Content-Type"] == "application/json"

    def test_censor_password_field(self):
        """Test that password fields are censored."""
        event_dict = {
            "message": "User login",
            "username": "john_doe",
            "password": "super_secret",
        }

        result = censor_sensitive_data(None, "info", event_dict)

        assert result["password"] == "***REDACTED***"
        assert result["username"] == "john_doe"

    def test_censor_case_insensitive(self):
        """Test that censoring is case-insensitive."""
        event_dict = {
            "message": "Making request",
            "ApiKey": "secret123",
            "API_KEY": "secret456",
        }

        result = censor_sensitive_data(None, "info", event_dict)

        assert result["ApiKey"] == "***REDACTED***"
        assert result["API_KEY"] == "***REDACTED***"
