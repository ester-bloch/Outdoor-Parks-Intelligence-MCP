"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

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
    Contacts,
    EmailAddress,
    EventData,
    NPSResponse,
    ParkData,
    PhoneNumber,
    VisitorCenterData,
)


class TestRequestModels:
    """Test request models."""

    def test_find_parks_request_valid(self):
        """Test FindParksRequest with valid data."""
        request = FindParksRequest(
            stateCode="CA", q="yosemite", limit=10, start=0, activities="hiking"
        )
        assert request.state_code == "CA"
        assert request.q == "yosemite"
        assert request.limit == 10
        assert request.start == 0
        assert request.activities == "hiking"

    def test_find_parks_request_snake_case(self):
        """Test FindParksRequest with snake_case fields."""
        request = FindParksRequest(
            state_code="CA", q="yosemite", limit=10, start=0, activities="hiking"
        )
        assert request.state_code == "CA"

    def test_find_parks_request_limit_validation(self):
        """Test FindParksRequest limit validation."""
        with pytest.raises(ValidationError):
            FindParksRequest(limit=0)  # Below minimum

        with pytest.raises(ValidationError):
            FindParksRequest(limit=51)  # Above maximum

    def test_get_park_details_request_valid(self):
        """Test GetParkDetailsRequest with valid data."""
        request = GetParkDetailsRequest(parkCode="yose")
        assert request.park_code == "yose"

    def test_get_park_details_request_required(self):
        """Test GetParkDetailsRequest requires park_code."""
        with pytest.raises(ValidationError):
            GetParkDetailsRequest()

    def test_get_alerts_request_valid(self):
        """Test GetAlertsRequest with valid data."""
        request = GetAlertsRequest(parkCode="yose", limit=10, start=0, q="closure")
        assert request.park_code == "yose"
        assert request.limit == 10
        assert request.start == 0
        assert request.q == "closure"

    def test_get_visitor_centers_request_valid(self):
        """Test GetVisitorCentersRequest with valid data."""
        request = GetVisitorCentersRequest(parkCode="yose", limit=10)
        assert request.park_code == "yose"
        assert request.limit == 10

    def test_get_campgrounds_request_valid(self):
        """Test GetCampgroundsRequest with valid data."""
        request = GetCampgroundsRequest(parkCode="yose", limit=10)
        assert request.park_code == "yose"
        assert request.limit == 10

    def test_get_events_request_valid(self):
        """Test GetEventsRequest with valid data."""
        request = GetEventsRequest(
            parkCode="yose",
            limit=10,
            dateStart="2024-01-01",
            dateEnd="2024-12-31",
        )
        assert request.park_code == "yose"
        assert request.limit == 10
        assert request.date_start == "2024-01-01"
        assert request.date_end == "2024-12-31"


class TestResponseModels:
    """Test response models."""

    def test_contacts_model(self):
        """Test Contacts model."""
        contacts = Contacts(
            phoneNumbers=[
                {
                    "phoneNumber": "123-456-7890",
                    "description": "Main",
                    "extension": "",
                    "type": "Voice",
                }
            ],
            emailAddresses=[
                {"description": "General", "emailAddress": "test@example.com"}
            ],
        )
        assert len(contacts.phone_numbers) == 1
        assert len(contacts.email_addresses) == 1
        assert contacts.phone_numbers[0].phone_number == "123-456-7890"
        assert contacts.email_addresses[0].email_address == "test@example.com"

    def test_alert_data_model(self):
        """Test AlertData model."""
        alert = AlertData(
            id="123",
            url="https://example.com",
            title="Test Alert",
            parkCode="yose",
            description="Test description",
            category="Closure",
            lastIndexedDate="2024-01-01",
        )
        assert alert.id == "123"
        assert alert.park_code == "yose"
        assert alert.category == "Closure"

    def test_nps_response_generic(self):
        """Test NPSResponse generic model."""
        response = NPSResponse[AlertData](
            total="1",
            limit="10",
            start="0",
            data=[
                AlertData(
                    id="123",
                    url="https://example.com",
                    title="Test Alert",
                    parkCode="yose",
                    description="Test description",
                    category="Closure",
                    lastIndexedDate="2024-01-01",
                )
            ],
        )
        assert response.total == "1"
        assert len(response.data) == 1
        assert response.data[0].park_code == "yose"


class TestErrorModels:
    """Test error models."""

    def test_error_response(self):
        """Test ErrorResponse model."""
        error = ErrorResponse(
            error="api_error",
            message="API request failed",
            details={"status_code": 500},
        )
        assert error.error == "api_error"
        assert error.message == "API request failed"
        assert error.details["status_code"] == 500

    def test_validation_error_response(self):
        """Test ValidationErrorResponse model."""
        error = ValidationErrorResponse(
            message="Validation failed",
            validation_errors=[
                {"loc": ["field"], "msg": "Field required", "type": "value_error"}
            ],
        )
        assert error.error == "validation_error"
        assert error.message == "Validation failed"
        assert len(error.validation_errors) == 1
