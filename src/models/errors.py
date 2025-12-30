"""Pydantic models for error responses."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    """Enumeration of error types for categorization."""

    # Validation errors
    VALIDATION_ERROR = "validation_error"
    INVALID_INPUT = "invalid_input"

    # API errors
    API_ERROR = "api_error"
    HTTP_ERROR = "http_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    PARSE_ERROR = "parse_error"

    # Authentication errors
    AUTH_ERROR = "authentication_error"
    MISSING_API_KEY = "missing_api_key"

    # Rate limiting errors
    RATE_LIMIT_ERROR = "rate_limit_error"

    # Resource errors
    NOT_FOUND = "not_found"
    RESOURCE_NOT_FOUND = "resource_not_found"

    # Server errors
    INTERNAL_ERROR = "internal_error"
    UNKNOWN_ERROR = "unknown_error"


class HTTPStatusCode:
    """HTTP status codes for error responses."""

    # Success
    OK = 200

    # Client errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429

    # Server errors
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    status_code: Optional[int] = Field(
        None, description="HTTP status code associated with the error"
    )

    @classmethod
    def from_exception(
        cls,
        error_type: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> "ErrorResponse":
        """
        Create an ErrorResponse from exception details.

        Args:
            error_type: Type of error (use ErrorType enum values)
            message: Human-readable error message
            status_code: HTTP status code
            details: Additional error details

        Returns:
            ErrorResponse instance
        """
        return cls(
            error=error_type,
            message=message,
            status_code=status_code,
            details=details or {},
        )


class ValidationError(BaseModel):
    """Individual validation error model."""

    loc: List[str] = Field(..., description="Location of the validation error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""

    error: str = Field(default="validation_error", description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    validation_errors: List[ValidationError] = Field(
        ..., description="List of validation errors"
    )
    status_code: int = Field(
        default=HTTPStatusCode.UNPROCESSABLE_ENTITY,
        description="HTTP status code (422 for validation errors)",
    )

    @classmethod
    def from_pydantic_error(cls, exc: Exception) -> "ValidationErrorResponse":
        """
        Create a ValidationErrorResponse from a Pydantic ValidationError.

        Args:
            exc: Pydantic ValidationError exception

        Returns:
            ValidationErrorResponse instance
        """
        errors = []
        if hasattr(exc, "errors"):
            for error in exc.errors():
                errors.append(
                    ValidationError(
                        loc=[str(loc) for loc in error.get("loc", [])],
                        msg=error.get("msg", "Validation error"),
                        type=error.get("type", "value_error"),
                    )
                )

        return cls(
            error=ErrorType.VALIDATION_ERROR,
            message="Input validation failed",
            validation_errors=errors,
        )
