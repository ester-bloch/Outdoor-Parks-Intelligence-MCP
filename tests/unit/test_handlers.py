"""Unit tests for handler error handling."""

from unittest.mock import MagicMock, patch

from src.handlers.get_campgrounds import get_campgrounds
from src.handlers.get_events import get_events
from src.models.requests import GetCampgroundsRequest, GetEventsRequest


@patch("src.handlers.get_campgrounds.get_client")
def test_get_campgrounds_with_one_invalid_item(mock_get_client):
    """Test that getCampgrounds handles one invalid item gracefully."""
    valid_campground = {
        "id": "valid-1",
        "url": "http://example.com",
        "name": "Valid Campground",
        "parkCode": "test",
        "description": "A valid campground",
        "latitude": "0",
        "longitude": "0",
        "latLong": "0,0",
        "audioDescription": "",
        "isPassportStampLocation": False,
        "passportStampLocationDescription": "",
        "passportStampImages": [],
        "geometryPoiId": "",
        "reservationInfo": "",
        "reservationUrl": "",
        "regulationsurl": "",
        "regulationsOverview": "",
        "amenities": {
            "trashRecyclingCollection": "Yes",
            "toilets": [],
            "internetConnectivity": False,
            "showers": [],
            "cellPhoneReception": "No",
            "laundry": False,
            "amphitheater": False,
            "dumpStation": False,
            "campStore": False,
            "staffOrVolunteerHostOnsite": "Yes",
            "potableWater": [],
            "iceAvailableForSale": False,
            "firewoodForSale": False,
            "foodStorageLockers": "No",
        },
        "contacts": {"phoneNumbers": [], "emailAddresses": []},
        "fees": [],
        "directionsOverview": "",
        "directionsUrl": "",
        "operatingHours": [],
        "addresses": [],
        "weatherOverview": "",
        "numberOfSitesReservable": "0",
        "numberOfSitesFirstComeFirstServe": "0",
        "campsites": {
            "totalSites": "0",
            "group": "0",
            "horse": "0",
            "tentOnly": "0",
            "electricalHookups": "0",
            "rvOnly": "0",
            "walkBoatTo": "0",
            "other": "0",
        },
        "accessibility": {
            "wheelchairAccess": "",
            "internetInfo": "",
            "cellPhoneInfo": "",
            "fireStovePolicy": "",
            "rvAllowed": False,
            "rvInfo": "",
            "rvMaxLength": "",
            "additionalInfo": "",
            "trailerMaxLength": "",
            "adaInfo": "",
            "trailerAllowed": False,
            "accessRoads": [],
            "classifications": [],
        },
    }

    invalid_campground = {"id": "invalid-1"}

    mock_client = MagicMock()
    mock_client.get_campgrounds.return_value = {
        "total": "2",
        "limit": "10",
        "start": "0",
        "data": [valid_campground, invalid_campground],
    }
    mock_get_client.return_value = mock_client

    request = GetCampgroundsRequest(park_code="test")
    result = get_campgrounds(request)

    assert len(result["campgrounds"]) == 1
    assert result["campgrounds"][0]["name"] == "Valid Campground"
    assert result["total"] == 2
    assert result["limit"] == 10
    assert result["start"] == 0


@patch("src.handlers.get_events.get_client")
def test_get_events_with_one_invalid_item(mock_get_client):
    """Test that getEvents handles one invalid item gracefully."""
    valid_event = {
        "id": "valid-1",
        "title": "Valid Event",
        "url": "http://example.com",
        "parkFullName": "Test Park",
        "description": "A valid event",
        "parkCode": "test",
    }

    invalid_event = {"id": "invalid-1"}

    mock_client = MagicMock()
    mock_client.get_events.return_value = {
        "total": "2",
        "limit": "10",
        "start": "0",
        "data": [valid_event, invalid_event],
    }
    mock_get_client.return_value = mock_client

    request = GetEventsRequest(park_code="test")
    result = get_events(request)

    assert len(result["events"]) == 1
    assert result["events"][0]["title"] == "Valid Event"
    assert result["total"] == 2
    assert result["limit"] == 10
    assert result["start"] == 0


@patch("src.handlers.get_campgrounds.get_client")
def test_get_campgrounds_empty_response(mock_get_client):
    """Test that getCampgrounds handles empty response correctly."""
    mock_client = MagicMock()
    mock_client.get_campgrounds.return_value = {
        "total": "0",
        "limit": "10",
        "start": "0",
        "data": [],
    }
    mock_get_client.return_value = mock_client

    request = GetCampgroundsRequest(park_code="test")
    result = get_campgrounds(request)

    assert len(result["campgrounds"]) == 0
    assert result["total"] == 0
    assert result["limit"] == 10
    assert result["start"] == 0


@patch("src.handlers.get_events.get_client")
def test_get_events_empty_response(mock_get_client):
    """Test that getEvents handles empty response correctly."""
    mock_client = MagicMock()
    mock_client.get_events.return_value = {
        "total": "0",
        "limit": "10",
        "start": "0",
        "data": [],
    }
    mock_get_client.return_value = mock_client

    request = GetEventsRequest(park_code="test")
    result = get_events(request)

    assert len(result["events"]) == 0
    assert result["total"] == 0
    assert result["limit"] == 10
    assert result["start"] == 0


@patch("src.handlers.get_campgrounds.get_client")
def test_get_campgrounds_all_items_invalid(mock_get_client):
    """Test that getCampgrounds handles all invalid items gracefully."""
    invalid_campgrounds = [
        {"id": "invalid-1"},
        {"id": "invalid-2"},
        {"id": "invalid-3"},
    ]

    mock_client = MagicMock()
    mock_client.get_campgrounds.return_value = {
        "total": "3",
        "limit": "10",
        "start": "0",
        "data": invalid_campgrounds,
    }
    mock_get_client.return_value = mock_client

    request = GetCampgroundsRequest(park_code="test")
    result = get_campgrounds(request)

    assert len(result["campgrounds"]) == 0
    assert result["total"] == 3
    assert result["limit"] == 10
    assert result["start"] == 0


@patch("src.handlers.get_events.get_client")
def test_get_events_all_items_invalid(mock_get_client):
    """Test that getEvents handles all invalid items gracefully."""
    invalid_events = [
        {"id": "invalid-1"},
        {"id": "invalid-2"},
        {"id": "invalid-3"},
    ]

    mock_client = MagicMock()
    mock_client.get_events.return_value = {
        "total": "3",
        "limit": "10",
        "start": "0",
        "data": invalid_events,
    }
    mock_get_client.return_value = mock_client

    request = GetEventsRequest(park_code="test")
    result = get_events(request)

    assert len(result["events"]) == 0
    assert result["total"] == 3
    assert result["limit"] == 10
    assert result["start"] == 0
