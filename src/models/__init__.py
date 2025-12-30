"""Data models for the National Parks MCP Server."""

from src.models.errors import ErrorResponse, ValidationErrorResponse
from src.models.requests import (
    FindParksRequest,
    GetAlertsRequest,
    GetCampgroundsRequest,
    GetEventsRequest,
    GetParkDetailsRequest,
    GetVisitorCentersRequest,
)
from src.models.responses import (
    AlertData,
    CampgroundData,
    EventData,
    NPSResponse,
    ParkData,
    VisitorCenterData,
)

__all__ = [
    # Request models
    "FindParksRequest",
    "GetParkDetailsRequest",
    "GetAlertsRequest",
    "GetVisitorCentersRequest",
    "GetCampgroundsRequest",
    "GetEventsRequest",
    # Response models
    "NPSResponse",
    "ParkData",
    "AlertData",
    "VisitorCenterData",
    "CampgroundData",
    "EventData",
    # Error models
    "ErrorResponse",
    "ValidationErrorResponse",
]
