"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add application context to log events.

    Args:
        logger: Logger instance
        method_name: Method name being called
        event_dict: Event dictionary

    Returns:
        Updated event dictionary with app context
    """
    event_dict["app"] = "python-mcp-nationalparks"
    return event_dict


def add_log_level(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add log level to event dictionary.

    Args:
        logger: Logger instance
        method_name: Method name being called
        event_dict: Event dictionary

    Returns:
        Updated event dictionary with log level
    """
    if method_name == "warn":
        # Normalize 'warn' to 'warning'
        event_dict["level"] = "warning"
    else:
        event_dict["level"] = method_name
    return event_dict


def censor_sensitive_data(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Censor sensitive data from logs (API keys, tokens, etc.).

    Args:
        logger: Logger instance
        method_name: Method name being called
        event_dict: Event dictionary

    Returns:
        Updated event dictionary with censored data
    """
    sensitive_keys = {
        "api_key",
        "apiKey",
        "X-Api-Key",
        "authorization",
        "password",
        "token",
    }

    for key in list(event_dict.keys()):
        if key.lower() in {k.lower() for k in sensitive_keys}:
            event_dict[key] = "***REDACTED***"
        elif isinstance(event_dict[key], dict):
            # Recursively censor nested dictionaries
            event_dict[key] = _censor_dict(event_dict[key], sensitive_keys)

    return event_dict


def _censor_dict(data: Dict[str, Any], sensitive_keys: set) -> Dict[str, Any]:
    """
    Recursively censor sensitive keys in a dictionary.

    Args:
        data: Dictionary to censor
        sensitive_keys: Set of sensitive key names

    Returns:
        Censored dictionary
    """
    censored = {}
    for key, value in data.items():
        if key.lower() in {k.lower() for k in sensitive_keys}:
            censored[key] = "***REDACTED***"
        elif isinstance(value, dict):
            censored[key] = _censor_dict(value, sensitive_keys)
        elif isinstance(value, list):
            censored[key] = [
                _censor_dict(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            censored[key] = value
    return censored


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
    include_timestamp: bool = True,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
        include_timestamp: Whether to include timestamps in logs
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=numeric_level,
    )

    # Build processor chain
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_app_context,
        add_log_level,
        structlog.stdlib.add_logger_name,
        censor_sensitive_data,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add timestamp if requested
    if include_timestamp:
        processors.append(structlog.processors.TimeStamper(fmt="iso"))

    # Add appropriate renderer based on format preference
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=False,  # Disable colors for MCP stdio transport
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def log_request(
    logger: structlog.stdlib.BoundLogger,
    tool_name: str,
    params: Dict[str, Any],
) -> None:
    """
    Log an incoming tool request.

    Args:
        logger: Logger instance
        tool_name: Name of the tool being called
        params: Request parameters
    """
    logger.info(
        "tool_request",
        tool=tool_name,
        params=params,
        event_type="request",
    )


def log_response(
    logger: structlog.stdlib.BoundLogger,
    tool_name: str,
    success: bool,
    response_size: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log a tool response.

    Args:
        logger: Logger instance
        tool_name: Name of the tool that was called
        success: Whether the request was successful
        response_size: Size of the response (e.g., number of results)
        error: Error message if request failed
    """
    log_data = {
        "tool": tool_name,
        "success": success,
        "event_type": "response",
    }

    if response_size is not None:
        log_data["response_size"] = response_size

    if error:
        log_data["error"] = error
        logger.warning("tool_response", **log_data)
    else:
        logger.info("tool_response", **log_data)


def log_api_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an outgoing API request.

    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL
        params: Query parameters
    """
    logger.debug(
        "api_request",
        method=method,
        url=url,
        params=params or {},
        event_type="api_request",
    )


def log_api_response(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    url: str,
    status_code: int,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """
    Log an API response.

    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        error: Error message if request failed
    """
    log_data = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "event_type": "api_response",
    }

    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)

    if error:
        log_data["error"] = error
        logger.error("api_response", **log_data)
    elif status_code >= 400:
        logger.warning("api_response", **log_data)
    else:
        logger.debug("api_response", **log_data)
