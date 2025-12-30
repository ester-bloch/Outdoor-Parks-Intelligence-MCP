"""Property-based tests for input validation consistency.

Feature: python-mcp-server, Property 4: Input Validation Consistency
Validates: Requirements 4.2, 4.4, 4.5
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from src.models.requests import (
    FindParksRequest,
    GetAlertsRequest,
    GetCampgroundsRequest,
    GetEventsRequest,
    GetParkDetailsRequest,
    GetVisitorCentersRequest,
)

# Property 4: Input Validation Consistency
# For any tool input (valid or invalid), the Python server should validate it
# before processing and return clear, structured error messages for validation failures


@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
@given(
    state_code=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    q=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
    limit=st.one_of(st.none(), st.integers(min_value=-10, max_value=100)),
    start=st.one_of(st.none(), st.integers(min_value=-10, max_value=1000)),
    activities=st.one_of(st.none(), st.text(min_size=0, max_size=50)),
)
def test_find_parks_validation_consistency(state_code, q, limit, start, activities):
    """
    Property: For any FindParksRequest input, validation should be consistent.

    Valid inputs (limit 1-50, start >= 0) should be accepted.
    Invalid inputs should raise ValidationError with clear messages.
    """
    try:
        request = FindParksRequest(
            stateCode=state_code,
            q=q,
            limit=limit,
            start=start,
            activities=activities,
        )
        # If validation succeeds, verify constraints are met
        if request.limit is not None:
            assert 1 <= request.limit <= 50, "Limit should be between 1 and 50"
        if request.start is not None:
            assert request.start >= 0, "Start should be non-negative"
    except ValidationError as e:
        # If validation fails, ensure error messages are clear and structured
        assert len(e.errors()) > 0, "ValidationError should contain error details"
        for error in e.errors():
            assert "loc" in error, "Error should have location"
            assert "msg" in error, "Error should have message"
            assert "type" in error, "Error should have type"
            assert isinstance(error["msg"], str), "Error message should be a string"
            assert len(error["msg"]) > 0, "Error message should not be empty"


@settings(max_examples=100)
@given(park_code=st.text(min_size=0, max_size=20))
def test_get_park_details_validation_consistency(park_code):
    """
    Property: For any GetParkDetailsRequest input, validation should be consistent.

    Non-empty park_code should be accepted.
    Empty park_code should raise ValidationError with clear messages.
    """
    try:
        request = GetParkDetailsRequest(parkCode=park_code)
        # If validation succeeds, park_code should not be empty
        assert len(request.park_code) > 0, "Park code should not be empty"
    except ValidationError as e:
        # If validation fails, ensure error messages are clear and structured
        assert len(e.errors()) > 0, "ValidationError should contain error details"
        for error in e.errors():
            assert "loc" in error, "Error should have location"
            assert "msg" in error, "Error should have message"
            assert "type" in error, "Error should have type"
            # Verify that empty strings are properly rejected
            if park_code == "":
                assert any(
                    "min_length" in str(error.get("type", ""))
                    or "string_too_short" in str(error.get("type", ""))
                    for error in e.errors()
                ), "Empty string should be rejected with min_length error"


@settings(max_examples=100)
@given(
    park_code=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    limit=st.one_of(st.none(), st.integers(min_value=-10, max_value=100)),
    start=st.one_of(st.none(), st.integers(min_value=-10, max_value=1000)),
    q=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
)
def test_get_alerts_validation_consistency(park_code, limit, start, q):
    """
    Property: For any GetAlertsRequest input, validation should be consistent.

    Valid inputs (limit 1-50, start >= 0) should be accepted.
    Invalid inputs should raise ValidationError with clear messages.
    """
    try:
        request = GetAlertsRequest(
            parkCode=park_code,
            limit=limit,
            start=start,
            q=q,
        )
        # If validation succeeds, verify constraints are met
        if request.limit is not None:
            assert 1 <= request.limit <= 50, "Limit should be between 1 and 50"
        if request.start is not None:
            assert request.start >= 0, "Start should be non-negative"
    except ValidationError as e:
        # If validation fails, ensure error messages are clear and structured
        assert len(e.errors()) > 0, "ValidationError should contain error details"
        for error in e.errors():
            assert "loc" in error, "Error should have location"
            assert "msg" in error, "Error should have message"
            assert "type" in error, "Error should have type"


@settings(max_examples=100)
@given(
    park_code=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    limit=st.one_of(st.none(), st.integers(min_value=-10, max_value=100)),
    start=st.one_of(st.none(), st.integers(min_value=-10, max_value=1000)),
    q=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
)
def test_get_visitor_centers_validation_consistency(park_code, limit, start, q):
    """
    Property: For any GetVisitorCentersRequest input, validation should be consistent.

    Valid inputs (limit 1-50, start >= 0) should be accepted.
    Invalid inputs should raise ValidationError with clear messages.
    """
    try:
        request = GetVisitorCentersRequest(
            parkCode=park_code,
            limit=limit,
            start=start,
            q=q,
        )
        # If validation succeeds, verify constraints are met
        if request.limit is not None:
            assert 1 <= request.limit <= 50, "Limit should be between 1 and 50"
        if request.start is not None:
            assert request.start >= 0, "Start should be non-negative"
    except ValidationError as e:
        # If validation fails, ensure error messages are clear and structured
        assert len(e.errors()) > 0, "ValidationError should contain error details"
        for error in e.errors():
            assert "loc" in error, "Error should have location"
            assert "msg" in error, "Error should have message"
            assert "type" in error, "Error should have type"


@settings(max_examples=100)
@given(
    park_code=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    limit=st.one_of(st.none(), st.integers(min_value=-10, max_value=100)),
    start=st.one_of(st.none(), st.integers(min_value=-10, max_value=1000)),
    q=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
)
def test_get_campgrounds_validation_consistency(park_code, limit, start, q):
    """
    Property: For any GetCampgroundsRequest input, validation should be consistent.

    Valid inputs (limit 1-50, start >= 0) should be accepted.
    Invalid inputs should raise ValidationError with clear messages.
    """
    try:
        request = GetCampgroundsRequest(
            parkCode=park_code,
            limit=limit,
            start=start,
            q=q,
        )
        # If validation succeeds, verify constraints are met
        if request.limit is not None:
            assert 1 <= request.limit <= 50, "Limit should be between 1 and 50"
        if request.start is not None:
            assert request.start >= 0, "Start should be non-negative"
    except ValidationError as e:
        # If validation fails, ensure error messages are clear and structured
        assert len(e.errors()) > 0, "ValidationError should contain error details"
        for error in e.errors():
            assert "loc" in error, "Error should have location"
            assert "msg" in error, "Error should have message"
            assert "type" in error, "Error should have type"


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    park_code=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    limit=st.one_of(st.none(), st.integers(min_value=-10, max_value=100)),
    start=st.one_of(st.none(), st.integers(min_value=-10, max_value=1000)),
    date_start=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    date_end=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    q=st.one_of(st.none(), st.text(min_size=0, max_size=100)),
)
def test_get_events_validation_consistency(
    park_code, limit, start, date_start, date_end, q
):
    """
    Property: For any GetEventsRequest input, validation should be consistent.

    Valid inputs (limit 1-50, start >= 0) should be accepted.
    Invalid inputs should raise ValidationError with clear messages.
    """
    try:
        request = GetEventsRequest(
            parkCode=park_code,
            limit=limit,
            start=start,
            dateStart=date_start,
            dateEnd=date_end,
            q=q,
        )
        # If validation succeeds, verify constraints are met
        if request.limit is not None:
            assert 1 <= request.limit <= 50, "Limit should be between 1 and 50"
        if request.start is not None:
            assert request.start >= 0, "Start should be non-negative"
    except ValidationError as e:
        # If validation fails, ensure error messages are clear and structured
        assert len(e.errors()) > 0, "ValidationError should contain error details"
        for error in e.errors():
            assert "loc" in error, "Error should have location"
            assert "msg" in error, "Error should have message"
            assert "type" in error, "Error should have type"
