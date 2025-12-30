"""Centralized error handling utilities for consistent error responses."""

from typing import Any, Dict, Optional, Type

from pydantic import ValidationError as PydanticValidationError

from src.api.client import NPSAPIError
from src.models.errors import (
    ErrorResponse,
    ErrorType,
    HTTPStatusCode,
    ValidationError,
    ValidationErrorResponse,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


def handle_validation_error(exc: PydanticValidationError) -> Dict[str, Any]:
    """
    Handle Pydantic validation errors and return structured response.

    Args:
        exc: Pydantic ValidationError

    Returns:
        Dictionary with validation error response
    """
    logger.warning(
        "validation_error",
        error_count=len(exc.errors()),
        message="Input validation failed",
    )

    errors = []
    for error in exc.errors():
        errors.append(
            ValidationError(
                loc=[str(loc) for loc in error.get("loc", [])],
                msg=error.get("msg", "Validation error"),
                type=error.get("type", "value_error"),
            )
        )

    response = ValidationErrorResponse(
        error=ErrorType.VALIDATION_ERROR,
        message="Input validation failed",
        validation_errors=errors,
        status_code=HTTPStatusCode.UNPROCESSABLE_ENTITY,
    )

    return response.model_dump()


def handle_api_error(exc: NPSAPIError) -> Dict[str, Any]:
    """
    Handle NPS API errors and return structured response.

    Args:
        exc: NPSAPIError exception

    Returns:
        Dictionary with error response
    """
    logger.error(
        "api_error",
        error_type=exc.error_type,
        status_code=exc.status_code,
        message=exc.message,
    )

    response = ErrorResponse(
        error=exc.error_type,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )

    return response.model_dump()


def handle_generic_error(
    exc: Exception,
    error_type: str = ErrorType.INTERNAL_ERROR,
    status_code: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Handle generic exceptions and return structured response.

    Args:
        exc: Exception to handle
        error_type: Type of error (from ErrorType enum)
        status_code: HTTP status code
        context: Additional context information

    Returns:
        Dictionary with error response
    """
    logger.error(
        "generic_error",
        error_type=error_type,
        error_message=str(exc),
        exc_info=True,
    )

    details = context or {}
    details["error_class"] = exc.__class__.__name__

    response = ErrorResponse(
        error=error_type,
        message=str(exc) or "An unexpected error occurred",
        status_code=status_code or HTTPStatusCode.INTERNAL_SERVER_ERROR,
        details=details,
    )

    return response.model_dump()


def handle_not_found_error(resource_type: str, resource_id: str) -> Dict[str, Any]:
    """
    Handle resource not found errors.

    Args:
        resource_type: Type of resource (e.g., "park", "alert")
        resource_id: ID of the resource

    Returns:
        Dictionary with error response
    """
    logger.warning(
        "resource_not_found",
        resource_type=resource_type,
        resource_id=resource_id,
    )

    # Format error message to match TypeScript implementation
    error_message = f"{resource_type.capitalize()} not found"

    response = ErrorResponse(
        error=error_message,
        message=f"{error_message}: No {resource_type} found with park code: {resource_id}",
        status_code=HTTPStatusCode.NOT_FOUND,
        details={
            "resource_type": resource_type,
            "resource_id": resource_id,
        },
    )

    return response.model_dump()


def handle_auth_error(message: str = "Authentication failed") -> Dict[str, Any]:
    """
    Handle authentication errors.

    Args:
        message: Error message

    Returns:
        Dictionary with error response
    """
    logger.error("auth_error", message=message)

    response = ErrorResponse(
        error=ErrorType.AUTH_ERROR,
        message=message,
        status_code=HTTPStatusCode.UNAUTHORIZED,
        details={},
    )

    return response.model_dump()


def handle_rate_limit_error(retry_after: Optional[int] = None) -> Dict[str, Any]:
    """
    Handle rate limit errors.

    Args:
        retry_after: Seconds to wait before retrying

    Returns:
        Dictionary with error response
    """
    logger.warning("rate_limit_error", retry_after=retry_after)

    details = {}
    if retry_after:
        details["retry_after"] = retry_after

    response = ErrorResponse(
        error=ErrorType.RATE_LIMIT_ERROR,
        message="Rate limit exceeded. Please try again later.",
        status_code=HTTPStatusCode.TOO_MANY_REQUESTS,
        details=details,
    )

    return response.model_dump()


def categorize_error(exc: Exception) -> tuple[str, int]:
    """
    Categorize an exception and return error type and status code.

    Args:
        exc: Exception to categorize

    Returns:
        Tuple of (error_type, status_code)
    """
    if isinstance(exc, PydanticValidationError):
        return ErrorType.VALIDATION_ERROR, HTTPStatusCode.UNPROCESSABLE_ENTITY
    elif isinstance(exc, NPSAPIError):
        return exc.error_type, exc.status_code or HTTPStatusCode.INTERNAL_SERVER_ERROR
    else:
        return ErrorType.INTERNAL_ERROR, HTTPStatusCode.INTERNAL_SERVER_ERROR
