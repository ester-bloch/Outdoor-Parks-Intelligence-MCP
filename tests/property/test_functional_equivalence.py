import json
from unittest.mock import Mock, patch

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.api.client import NPSAPIClient, NPSAPIError
from src.constants import STATE_CODES
from src.handlers.find_parks import find_parks
from src.handlers.get_park_details import get_park_details
from src.models.requests import FindParksRequest, GetParkDetailsRequest


@pytest.fixture(autouse=True)
def mock_api_client():
    """Mock the API client for all tests."""
    with patch("src.handlers.find_parks.get_client") as mock_find_parks, patch(
        "src.handlers.get_park_details.get_client"
    ) as mock_details, patch(
        "src.handlers.get_alerts.get_client"
    ) as mock_alerts, patch(
        "src.handlers.get_visitor_centers.get_client"
    ) as mock_centers, patch(
        "src.handlers.get_campgrounds.get_client"
    ) as mock_campgrounds, patch(
        "src.handlers.get_events.get_client"
    ) as mock_events:
        # Create a mock client
        mock_client = Mock(spec=NPSAPIClient)

        # Set up default responses
        mock_client.get_parks.return_value = {
            "total": "10",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "test-id",
                    "url": "https://www.nps.gov/test",
                    "fullName": "Test National Park",
                    "parkCode": "test",
                    "description": "A test park",
                    "latitude": "40.0",
                    "longitude": "-105.0",
                    "latLong": "lat:40.0, long:-105.0",
                    "states": "CO",
                    "contacts": {
                        "phoneNumbers": [
                            {
                                "phoneNumber": "1234567890",
                                "description": "",
                                "extension": "",
                                "type": "Voice",
                            }
                        ],
                        "emailAddresses": [
                            {"emailAddress": "test@nps.gov", "description": ""}
                        ],
                    },
                    "entranceFees": [
                        {"title": "Fee", "cost": "10.00", "description": "Test"}
                    ],
                    "entrancePasses": [
                        {"title": "Pass", "cost": "80.00", "description": "Test"}
                    ],
                    "fees": [],
                    "directionsInfo": "Test directions",
                    "directionsUrl": "https://www.nps.gov/test/directions",
                    "operatingHours": [
                        {
                            "name": "Test Park",
                            "description": "Open",
                            "standardHours": {
                                "sunday": "All Day",
                                "monday": "All Day",
                                "tuesday": "All Day",
                                "wednesday": "All Day",
                                "thursday": "All Day",
                                "friday": "All Day",
                                "saturday": "All Day",
                            },
                            "exceptions": [],
                        }
                    ],
                    "addresses": [
                        {
                            "postalCode": "80000",
                            "city": "Test",
                            "stateCode": "CO",
                            "countryCode": "US",
                            "provinceTerritoryCode": "",
                            "line1": "123 Test",
                            "line2": "",
                            "line3": "",
                            "type": "Physical",
                        }
                    ],
                    "images": [
                        {
                            "credit": "NPS",
                            "title": "Test",
                            "altText": "Test",
                            "caption": "Test",
                            "url": "https://test.jpg",
                        }
                    ],
                    "weatherInfo": "Test weather",
                    "name": "Test",
                    "designation": "National Park",
                    "activities": [{"id": "test", "name": "Hiking"}],
                    "topics": [{"id": "test", "name": "Nature"}],
                }
            ],
        }

        mock_client.get_park_by_code.return_value = mock_client.get_parks.return_value
        mock_client.get_alerts.return_value = {
            "total": "5",
            "limit": "10",
            "start": "0",
            "data": [],
        }
        mock_client.get_visitor_centers.return_value = {
            "total": "5",
            "limit": "10",
            "start": "0",
            "data": [],
        }
        mock_client.get_campgrounds.return_value = {
            "total": "5",
            "limit": "10",
            "start": "0",
            "data": [],
        }
        mock_client.get_events.return_value = {
            "total": "5",
            "limit": "10",
            "start": "0",
            "data": [],
        }

        # Return the same mock for all handlers
        mock_find_parks.return_value = mock_client
        mock_details.return_value = mock_client
        mock_alerts.return_value = mock_client
        mock_centers.return_value = mock_client
        mock_campgrounds.return_value = mock_client
        mock_events.return_value = mock_client

        yield mock_client


@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
@given(
    state_code=st.one_of(
        st.none(),
        st.sampled_from(STATE_CODES),
    ),
    limit=st.one_of(st.none(), st.integers(min_value=1, max_value=50)),
    q=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
)
def test_find_parks_response_structure(mock_api_client, state_code, limit, q):
    request = FindParksRequest(stateCode=state_code, q=q, limit=limit)
    result = find_parks(request)

    assert isinstance(result, dict), "Response should be a dictionary"
    assert "total" in result, "Response should have 'total' field"
    assert "limit" in result, "Response should have 'limit' field"
    assert "start" in result, "Response should have 'start' field"
    assert "parks" in result, "Response should have 'parks' field"

    assert isinstance(result["total"], int), "total should be an integer"
    assert isinstance(result["limit"], int), "limit should be an integer"
    assert isinstance(result["start"], int), "start should be an integer"
    assert isinstance(result["parks"], list), "parks should be a list"

    # Verify park object structure
    if len(result["parks"]) > 0:
        park = result["parks"][0]
        required_fields = [
            "name",
            "code",
            "description",
            "states",
            "url",
            "designation",
            "activities",
            "weatherInfo",
            "location",
            "entranceFees",
            "operatingHours",
            "contacts",
            "images",
        ]
        for field in required_fields:
            assert field in park, f"Park should have '{field}' field"


@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    state_code=st.text(min_size=1, max_size=10).filter(
        lambda x: x.upper() not in STATE_CODES and "," not in x
    )
)
def test_find_parks_invalid_state_error_handling(mock_api_client, state_code):
    request = FindParksRequest(stateCode=state_code)
    result = find_parks(request)

    assert isinstance(result, dict), "Error response should be a dictionary"
    assert "error" in result, "Error response should have 'error' field"
    assert (
        "validStateCodes" in result
    ), "Error response should have 'validStateCodes' field"
    assert (
        "Invalid state code" in result["error"]
    ), "Error should mention invalid state code"
    assert isinstance(
        result["validStateCodes"], list
    ), "validStateCodes should be a list"


@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(park_code=st.text(min_size=1, max_size=10))
def test_get_park_details_response_structure(mock_api_client, park_code):
    request = GetParkDetailsRequest(parkCode=park_code)
    result = get_park_details(request)

    assert isinstance(result, dict), "Response should be a dictionary"

    required_fields = [
        "name",
        "code",
        "url",
        "description",
        "designation",
        "states",
        "weatherInfo",
        "directionsInfo",
        "directionsUrl",
        "location",
        "contacts",
        "entranceFees",
        "entrancePasses",
        "operatingHours",
        "topics",
        "activities",
        "images",
    ]
    for field in required_fields:
        assert field in result, f"Park details should have '{field}' field"

    # Verify location structure
    assert "latitude" in result["location"], "Location should have latitude"
    assert "longitude" in result["location"], "Location should have longitude"


@settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(park_code=st.text(min_size=1, max_size=10))
def test_get_park_details_not_found_error(mock_api_client, park_code):
    # Configure mock to return empty data
    mock_api_client.get_park_by_code.return_value = {
        "total": "0",
        "limit": "1",
        "start": "0",
        "data": [],
    }

    request = GetParkDetailsRequest(parkCode=park_code)
    result = get_park_details(request)

    assert isinstance(result, dict), "Error response should be a dictionary"
    assert "error" in result, "Error response should have 'error' field"
    assert "message" in result, "Error response should have 'message' field"
    assert result["error"] == "Park not found", "Error should be 'Park not found'"
    assert park_code in result["message"], "Message should contain the park code"


@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    limit=st.one_of(st.none(), st.integers(min_value=1, max_value=50)),
)
def test_handler_response_serialization(mock_api_client, limit):
    from src.handlers.get_alerts import get_alerts
    from src.models.requests import GetAlertsRequest

    request = GetAlertsRequest(limit=limit)
    result = get_alerts(request)

    # Verify response is JSON serializable
    try:
        json_str = json.dumps(result)
        assert isinstance(json_str, str), "Result should be JSON serializable"

        # Verify it can be deserialized back
        deserialized = json.loads(json_str)
        assert isinstance(deserialized, dict), "Deserialized result should be a dict"
    except (TypeError, ValueError) as e:
        pytest.fail(f"Response should be JSON serializable: {e}")


@settings(max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    limit=st.integers(min_value=1, max_value=50),
    start=st.integers(min_value=0, max_value=100),
)
def test_pagination_parameters_consistency(mock_api_client, limit, start):
    from src.handlers.get_visitor_centers import get_visitor_centers
    from src.models.requests import GetVisitorCentersRequest

    # Configure mock to return pagination values
    mock_api_client.get_visitor_centers.return_value = {
        "total": "100",
        "limit": str(limit),
        "start": str(start),
        "data": [],
    }

    request = GetVisitorCentersRequest(limit=limit, start=start)
    result = get_visitor_centers(request)

    assert "total" in result, "Response should have 'total' field"
    assert "limit" in result, "Response should have 'limit' field"
    assert "start" in result, "Response should have 'start' field"

    assert isinstance(result["total"], int), "total should be an integer"
    assert isinstance(result["limit"], int), "limit should be an integer"
    assert isinstance(result["start"], int), "start should be an integer"

    # Verify values match input
    assert result["limit"] == limit, "limit should match input"
    assert result["start"] == start, "start should match input"


def test_all_handlers_have_consistent_error_handling(mock_api_client):
    from src.handlers.get_campgrounds import get_campgrounds
    from src.handlers.get_events import get_events
    from src.models.requests import GetCampgroundsRequest, GetEventsRequest

    handlers_and_requests = [
        (find_parks, FindParksRequest()),
        (get_park_details, GetParkDetailsRequest(parkCode="test")),
        (get_campgrounds, GetCampgroundsRequest()),
        (get_events, GetEventsRequest()),
    ]

    for handler, request in handlers_and_requests:
        # Configure mock to raise API error
        mock_api_client.get_parks.side_effect = NPSAPIError(
            message="API Error", status_code=500, error_type="api_error"
        )
        mock_api_client.get_park_by_code.side_effect = NPSAPIError(
            message="API Error", status_code=500, error_type="api_error"
        )
        mock_api_client.get_campgrounds.side_effect = NPSAPIError(
            message="API Error", status_code=500, error_type="api_error"
        )
        mock_api_client.get_events.side_effect = NPSAPIError(
            message="API Error", status_code=500, error_type="api_error"
        )

        with pytest.raises(NPSAPIError) as exc_info:
            handler(request)

        # Verify error has proper structure
        error = exc_info.value
        assert hasattr(error, "message"), "Error should have message"
        assert hasattr(error, "status_code"), "Error should have status_code"
        assert hasattr(error, "error_type"), "Error should have error_type"
