"""Property-based tests for graceful degradation in handlers.

Feature: mcp-validation-fixes
Tests Properties 8 and 9 from the design document.
"""

from unittest.mock import MagicMock, patch

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.handlers.get_campgrounds import get_campgrounds
from src.handlers.get_events import get_events
from src.models.requests import GetCampgroundsRequest, GetEventsRequest


# Strategy for generating valid campground data
@st.composite
def valid_campground_data(draw):
    """Generate valid campground data."""
    return {
        "id": draw(st.text(min_size=1, max_size=10)),
        "url": draw(st.text(min_size=1)),
        "name": draw(st.text(min_size=1)),
        "parkCode": draw(st.text(min_size=2, max_size=4)),
        "description": draw(st.text()),
        "latitude": draw(st.text()),
        "longitude": draw(st.text()),
        "latLong": draw(st.text()),
        "audioDescription": draw(st.text()),
        "isPassportStampLocation": draw(st.booleans()),
        "passportStampLocationDescription": draw(st.text()),
        "passportStampImages": [],
        "geometryPoiId": draw(st.text()),
        "reservationInfo": draw(st.text()),
        "reservationUrl": draw(st.text()),
        "regulationsurl": draw(st.text()),
        "regulationsOverview": draw(st.text()),
        "amenities": {
            "trashRecyclingCollection": draw(st.sampled_from(["Yes", "No", None])),
            "toilets": [],
            "internetConnectivity": draw(st.booleans()),
            "showers": [],
            "cellPhoneReception": draw(st.sampled_from(["Yes", "No", None])),
            "laundry": draw(st.booleans()),
            "amphitheater": draw(st.booleans()),
            "dumpStation": draw(st.booleans()),
            "campStore": draw(st.booleans()),
            "staffOrVolunteerHostOnsite": draw(st.sampled_from(["Yes", "No", None])),
            "potableWater": [],
            "iceAvailableForSale": draw(st.booleans()),
            "firewoodForSale": draw(st.booleans()),
            "foodStorageLockers": draw(st.sampled_from(["Yes", "No", None])),
        },
        "contacts": {
            "phoneNumbers": [],
            "emailAddresses": [],
        },
        "fees": [],
        "directionsOverview": draw(st.text()),
        "directionsUrl": draw(st.text()),
        "operatingHours": [],
        "addresses": [],
        "weatherOverview": draw(st.text()),
        "numberOfSitesReservable": draw(st.text()),
        "numberOfSitesFirstComeFirstServe": draw(st.text()),
        "campsites": {
            "totalSites": draw(st.text()),
            "group": draw(st.text()),
            "horse": draw(st.text()),
            "tentOnly": draw(st.text()),
            "electricalHookups": draw(st.text()),
            "rvOnly": draw(st.text()),
            "walkBoatTo": draw(st.text()),
            "other": draw(st.text()),
        },
        "accessibility": {
            "wheelchairAccess": draw(st.text()),
            "internetInfo": draw(st.text()),
            "cellPhoneInfo": draw(st.text()),
            "fireStovePolicy": draw(st.text()),
            "rvAllowed": draw(st.booleans()),
            "rvInfo": draw(st.text()),
            "rvMaxLength": draw(st.text()),
            "additionalInfo": draw(st.text()),
            "trailerMaxLength": draw(st.text()),
            "adaInfo": draw(st.text()),
            "trailerAllowed": draw(st.booleans()),
            "accessRoads": [],
            "classifications": [],
        },
    }


# Strategy for generating invalid campground data (missing required fields)
@st.composite
def invalid_campground_data(draw):
    """Generate invalid campground data by omitting required fields."""
    return {
        "id": draw(st.text(min_size=1, max_size=10)),
        # Missing required fields like 'name', 'parkCode', etc.
    }


# Strategy for generating valid event data
@st.composite
def valid_event_data(draw):
    """Generate valid event data."""
    return {
        "id": draw(st.text(min_size=1, max_size=10)),
        "title": draw(st.text(min_size=1)),
        "url": draw(st.text()),
        "parkFullName": draw(st.text()),
        "description": draw(st.text()),
        "latitude": draw(st.text()),
        "longitude": draw(st.text()),
        "category": draw(st.text()),
        "subcategory": draw(st.text()),
        "location": draw(st.text()),
        "tags": [],
        "recurrenceDateStart": draw(st.text()),
        "recurrenceDateEnd": draw(st.text()),
        "times": [],
        "dates": [],
        "dateStart": draw(st.text()),
        "dateEnd": draw(st.text()),
        "regresurl": draw(st.text()),
        "contactEmailAddress": draw(st.text()),
        "contactTelephoneNumber": draw(st.text()),
        "feeInfo": draw(st.text()),
        "isRecurring": draw(st.sampled_from(["Yes", "No", None])),
        "isAllDay": draw(st.sampled_from(["Yes", "No", None])),
        "siteCode": draw(st.text()),
        "parkCode": draw(st.text(min_size=2, max_size=4)),
        "organizationName": draw(st.text()),
        "types": [],
        "createDate": draw(st.text()),
        "lastUpdated": draw(st.text()),
        "infoURL": draw(st.text()),
        "portalName": draw(st.text()),
    }


# Strategy for generating invalid event data (missing required fields)
@st.composite
def invalid_event_data(draw):
    """Generate invalid event data by omitting required fields."""
    return {
        "id": draw(st.text(min_size=1, max_size=10)),
        # Missing required 'title' field
    }


# Feature: mcp-validation-fixes, Property 8: Graceful Degradation for Invalid Items
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_count=st.integers(min_value=1, max_value=5),
    data=st.data(),
)
@patch("src.handlers.get_campgrounds.get_client")
def test_campgrounds_graceful_degradation_with_mixed_items(
    mock_get_client, valid_count, invalid_count, data
):
    """Test graceful degradation with mixed valid and invalid items.

    Property 8: For any handler and for any list of items where some items fail
    validation, the handler should return only the valid items and continue
    processing without raising an exception.

    Validates: Requirements 4.1, 4.3, 4.4
    """
    # Generate mixed list of valid and invalid items
    valid_items = [data.draw(valid_campground_data()) for _ in range(valid_count)]
    invalid_items = [data.draw(invalid_campground_data()) for _ in range(invalid_count)]

    # Interleave valid and invalid items
    all_items = []
    for i in range(max(valid_count, invalid_count)):
        if i < valid_count:
            all_items.append(valid_items[i])
        if i < invalid_count:
            all_items.append(invalid_items[i])

    # Mock API response
    mock_client = MagicMock()
    mock_client.get_campgrounds.return_value = {
        "total": str(len(all_items)),
        "limit": "10",
        "start": "0",
        "data": all_items,
    }
    mock_get_client.return_value = mock_client

    # Call handler
    request = GetCampgroundsRequest(park_code="test")
    result = get_campgrounds(request)

    # Verify only valid items are returned
    assert len(result["campgrounds"]) == valid_count
    # Verify no exception was raised (test passes if we get here)


# Feature: mcp-validation-fixes, Property 8: Graceful Degradation for Invalid Items
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    valid_count=st.integers(min_value=1, max_value=5),
    invalid_count=st.integers(min_value=1, max_value=5),
    data=st.data(),
)
@patch("src.handlers.get_events.get_client")
def test_events_graceful_degradation_with_mixed_items(
    mock_get_client, valid_count, invalid_count, data
):
    """Test graceful degradation with mixed valid and invalid event items.

    Property 8: For any handler and for any list of items where some items fail
    validation, the handler should return only the valid items and continue
    processing without raising an exception.

    Validates: Requirements 4.2, 4.3, 4.4
    """
    # Generate mixed list of valid and invalid items
    valid_items = [data.draw(valid_event_data()) for _ in range(valid_count)]
    invalid_items = [data.draw(invalid_event_data()) for _ in range(invalid_count)]

    # Interleave valid and invalid items
    all_items = []
    for i in range(max(valid_count, invalid_count)):
        if i < valid_count:
            all_items.append(valid_items[i])
        if i < invalid_count:
            all_items.append(invalid_items[i])

    # Mock API response
    mock_client = MagicMock()
    mock_client.get_events.return_value = {
        "total": str(len(all_items)),
        "limit": "10",
        "start": "0",
        "data": all_items,
    }
    mock_get_client.return_value = mock_client

    # Call handler
    request = GetEventsRequest(park_code="test")
    result = get_events(request)

    # Verify only valid items are returned
    assert len(result["events"]) == valid_count
    # Verify no exception was raised (test passes if we get here)


# Feature: mcp-validation-fixes, Property 8: Graceful Degradation for Invalid Items (Edge Case)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_count=st.integers(min_value=1, max_value=10), data=st.data())
@patch("src.handlers.get_campgrounds.get_client")
def test_campgrounds_all_items_invalid(mock_get_client, invalid_count, data):
    """Test edge case when all campground items are invalid.

    Property 8 Edge Case: When all items fail validation, the handler should
    return an empty list without raising an exception.

    Validates: Requirements 4.1, 4.3
    """
    # Generate only invalid items
    invalid_items = [data.draw(invalid_campground_data()) for _ in range(invalid_count)]

    # Mock API response
    mock_client = MagicMock()
    mock_client.get_campgrounds.return_value = {
        "total": str(len(invalid_items)),
        "limit": "10",
        "start": "0",
        "data": invalid_items,
    }
    mock_get_client.return_value = mock_client

    # Call handler
    request = GetCampgroundsRequest(park_code="test")
    result = get_campgrounds(request)

    # Verify empty list is returned
    assert len(result["campgrounds"]) == 0
    # Verify no exception was raised (test passes if we get here)


# Feature: mcp-validation-fixes, Property 8: Graceful Degradation for Invalid Items (Edge Case)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_count=st.integers(min_value=1, max_value=10), data=st.data())
@patch("src.handlers.get_events.get_client")
def test_events_all_items_invalid(mock_get_client, invalid_count, data):
    """Test edge case when all event items are invalid.

    Property 8 Edge Case: When all items fail validation, the handler should
    return an empty list without raising an exception.

    Validates: Requirements 4.2, 4.3
    """
    # Generate only invalid items
    invalid_items = [data.draw(invalid_event_data()) for _ in range(invalid_count)]

    # Mock API response
    mock_client = MagicMock()
    mock_client.get_events.return_value = {
        "total": str(len(invalid_items)),
        "limit": "10",
        "start": "0",
        "data": invalid_items,
    }
    mock_get_client.return_value = mock_client

    # Call handler
    request = GetEventsRequest(park_code="test")
    result = get_events(request)

    # Verify empty list is returned
    assert len(result["events"]) == 0
    # Verify no exception was raised (test passes if we get here)


# Feature: mcp-validation-fixes, Property 9: Response Metadata Always Present
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    valid_count=st.integers(min_value=0, max_value=5),
    invalid_count=st.integers(min_value=0, max_value=5),
    data=st.data(),
)
@patch("src.handlers.get_campgrounds.get_client")
def test_campgrounds_metadata_always_present(
    mock_get_client, valid_count, invalid_count, data
):
    """Test that campground metadata is always present in response.

    Property 9: For any handler response, regardless of validation success or
    failure, the response should always include total, limit, and start fields.

    Validates: Requirements 4.5
    """
    # Generate mixed list (could be all valid, all invalid, or mixed)
    valid_items = [data.draw(valid_campground_data()) for _ in range(valid_count)]
    invalid_items = [data.draw(invalid_campground_data()) for _ in range(invalid_count)]
    all_items = valid_items + invalid_items

    # Mock API response
    mock_client = MagicMock()
    mock_client.get_campgrounds.return_value = {
        "total": str(len(all_items)),
        "limit": "10",
        "start": "0",
        "data": all_items,
    }
    mock_get_client.return_value = mock_client

    # Call handler
    request = GetCampgroundsRequest(park_code="test")
    result = get_campgrounds(request)

    # Verify metadata is always present
    assert "total" in result
    assert "limit" in result
    assert "start" in result
    assert isinstance(result["total"], int)
    assert isinstance(result["limit"], int)
    assert isinstance(result["start"], int)


# Feature: mcp-validation-fixes, Property 9: Response Metadata Always Present
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    valid_count=st.integers(min_value=0, max_value=5),
    invalid_count=st.integers(min_value=0, max_value=5),
    data=st.data(),
)
@patch("src.handlers.get_events.get_client")
def test_events_metadata_always_present(
    mock_get_client, valid_count, invalid_count, data
):
    """Test that event metadata is always present in response.

    Property 9: For any handler response, regardless of validation success or
    failure, the response should always include total, limit, and start fields.

    Validates: Requirements 4.5
    """
    # Generate mixed list (could be all valid, all invalid, or mixed)
    valid_items = [data.draw(valid_event_data()) for _ in range(valid_count)]
    invalid_items = [data.draw(invalid_event_data()) for _ in range(invalid_count)]
    all_items = valid_items + invalid_items

    # Mock API response
    mock_client = MagicMock()
    mock_client.get_events.return_value = {
        "total": str(len(all_items)),
        "limit": "10",
        "start": "0",
        "data": all_items,
    }
    mock_get_client.return_value = mock_client

    # Call handler
    request = GetEventsRequest(park_code="test")
    result = get_events(request)

    # Verify metadata is always present
    assert "total" in result
    assert "limit" in result
    assert "start" in result
    assert isinstance(result["total"], int)
    assert isinstance(result["limit"], int)
    assert isinstance(result["start"], int)
