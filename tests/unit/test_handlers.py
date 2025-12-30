"""Unit tests for tool handlers."""

from unittest.mock import Mock, patch

import pytest

from src.api.client import NPSAPIError
from src.handlers.get_park_details import get_park_details
from src.models.requests import GetParkDetailsRequest


class TestGetParkDetails:
    """Test get_park_details handler."""

    def test_get_park_details_success(self):
        """Test get_park_details with valid park code."""
        # Mock API response
        mock_response = {
            "total": "1",
            "limit": "1",
            "start": "0",
            "data": [
                {
                    "id": "77E0D7F0-1942-494A-ACE2-9004D2BDC59E",
                    "url": "https://www.nps.gov/yose/index.htm",
                    "fullName": "Yosemite National Park",
                    "parkCode": "yose",
                    "description": "Not just a great valley, but a shrine to human foresight...",
                    "latitude": "37.84883288",
                    "longitude": "-119.5571873",
                    "latLong": "lat:37.84883288, long:-119.5571873",
                    "activities": [{"id": "1", "name": "Hiking"}],
                    "topics": [{"id": "1", "name": "Geology"}],
                    "states": "CA",
                    "contacts": {
                        "phoneNumbers": [
                            {
                                "phoneNumber": "209-372-0200",
                                "description": "Main",
                                "extension": "",
                                "type": "Voice",
                            }
                        ],
                        "emailAddresses": [
                            {
                                "description": "General",
                                "emailAddress": "yose_web_manager@nps.gov",
                            }
                        ],
                    },
                    "entranceFees": [
                        {
                            "cost": "35.00",
                            "description": "7-day pass",
                            "title": "Entrance Fee",
                        }
                    ],
                    "entrancePasses": [],
                    "fees": [],
                    "directionsInfo": "You can drive to Yosemite...",
                    "directionsUrl": "http://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [
                        {
                            "exceptions": [],
                            "description": "Open year round",
                            "standardHours": {
                                "sunday": "All Day",
                                "monday": "All Day",
                                "tuesday": "All Day",
                                "wednesday": "All Day",
                                "thursday": "All Day",
                                "friday": "All Day",
                                "saturday": "All Day",
                            },
                            "name": "Yosemite National Park",
                        }
                    ],
                    "addresses": [
                        {
                            "postalCode": "95389",
                            "city": "Yosemite Valley",
                            "stateCode": "CA",
                            "line1": "9039 Village Drive",
                            "line2": "",
                            "line3": "",
                            "type": "Physical",
                        }
                    ],
                    "images": [
                        {
                            "credit": "NPS",
                            "title": "Yosemite Valley",
                            "altText": "Yosemite Valley",
                            "caption": "Yosemite Valley",
                            "url": "https://www.nps.gov/common/uploads/structured_data/image.jpg",
                        }
                    ],
                    "weatherInfo": "Yosemite National Park covers nearly 1,200 square miles...",
                    "name": "Yosemite",
                    "designation": "National Park",
                }
            ],
        }

        with patch("src.handlers.get_park_details.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_park_by_code.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetParkDetailsRequest(park_code="yose")
            result = get_park_details(request)

            # Verify the result structure
            assert "name" in result
            assert result["name"] == "Yosemite National Park"
            assert result["code"] == "yose"
            assert result["designation"] == "National Park"
            assert "location" in result
            assert "contacts" in result
            assert "entranceFees" in result
            assert "operatingHours" in result

            # Verify API was called correctly
            mock_client.get_park_by_code.assert_called_once_with("yose")

    def test_get_park_details_not_found(self):
        """Test get_park_details with invalid park code."""
        # Mock API response with no data
        mock_response = {"total": "0", "limit": "1", "start": "0", "data": []}

        with patch("src.handlers.get_park_details.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_park_by_code.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetParkDetailsRequest(park_code="invalid")
            result = get_park_details(request)

            # Verify error response
            assert "error" in result
            assert result["error"] == "Park not found"
            assert "invalid" in result["message"]

    def test_get_park_details_api_error(self):
        """Test get_park_details with API error."""
        with patch("src.handlers.get_park_details.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_park_by_code.side_effect = NPSAPIError(
                message="API request failed", status_code=500, error_type="api_error"
            )
            mock_get_client.return_value = mock_client

            request = GetParkDetailsRequest(park_code="yose")

            # Verify exception is raised
            with pytest.raises(NPSAPIError) as exc_info:
                get_park_details(request)

            assert exc_info.value.message == "API request failed"
            assert exc_info.value.status_code == 500


class TestGetAlerts:
    """Test get_alerts handler."""

    def test_get_alerts_success(self):
        """Test get_alerts with valid parameters."""
        # Mock API response
        mock_response = {
            "total": "2",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "alert1",
                    "url": "https://www.nps.gov/yose/planyourvisit/conditions.htm",
                    "title": "Road Closure",
                    "parkCode": "yose",
                    "description": "Tioga Road is closed for the season.",
                    "category": "Park Closure",
                    "lastIndexedDate": "2024-01-15T10:30:00Z",
                },
                {
                    "id": "alert2",
                    "url": "https://www.nps.gov/yose/planyourvisit/conditions.htm",
                    "title": "Bear Activity",
                    "parkCode": "yose",
                    "description": "Increased bear activity in the valley.",
                    "category": "Caution",
                    "lastIndexedDate": "2024-01-14T08:00:00Z",
                },
            ],
        }

        with patch("src.handlers.get_alerts.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_alerts.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_alerts import get_alerts
            from src.models.requests import GetAlertsRequest

            request = GetAlertsRequest(park_code="yose", limit=10)
            result = get_alerts(request)

            # Verify the result structure
            assert "total" in result
            assert result["total"] == 2
            assert result["limit"] == 10
            assert "alerts" in result
            assert len(result["alerts"]) == 2
            assert "alertsByPark" in result

            # Verify alert formatting
            alert = result["alerts"][0]
            assert "title" in alert
            assert "description" in alert
            assert "parkCode" in alert
            assert "type" in alert
            assert "lastUpdated" in alert
            assert alert["type"] == "Park Closure (area inaccessible)"

            # Verify alerts are grouped by park
            assert "yose" in result["alertsByPark"]
            assert len(result["alertsByPark"]["yose"]) == 2

            # Verify API was called correctly
            mock_client.get_alerts.assert_called_once()

    def test_get_alerts_with_search(self):
        """Test get_alerts with search query."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "alert1",
                    "url": "https://www.nps.gov/grca/planyourvisit/conditions.htm",
                    "title": "Trail Closure",
                    "parkCode": "grca",
                    "description": "Bright Angel Trail is closed due to ice.",
                    "category": "Information",
                    "lastIndexedDate": "2024-01-15T10:30:00Z",
                }
            ],
        }

        with patch("src.handlers.get_alerts.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_alerts.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_alerts import get_alerts
            from src.models.requests import GetAlertsRequest

            request = GetAlertsRequest(q="trail", limit=10)
            result = get_alerts(request)

            # Verify the result
            assert result["total"] == 1
            assert len(result["alerts"]) == 1
            assert result["alerts"][0]["type"] == "Information (non-emergency)"

    def test_get_alerts_empty_response(self):
        """Test get_alerts with no alerts found."""
        mock_response = {"total": "0", "limit": "10", "start": "0", "data": []}

        with patch("src.handlers.get_alerts.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_alerts.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_alerts import get_alerts
            from src.models.requests import GetAlertsRequest

            request = GetAlertsRequest(park_code="invalid")
            result = get_alerts(request)

            # Verify empty result
            assert result["total"] == 0
            assert len(result["alerts"]) == 0
            assert len(result["alertsByPark"]) == 0

    def test_get_alerts_api_error(self):
        """Test get_alerts with API error."""
        with patch("src.handlers.get_alerts.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_alerts.side_effect = NPSAPIError(
                message="API request failed", status_code=500, error_type="api_error"
            )
            mock_get_client.return_value = mock_client

            from src.handlers.get_alerts import get_alerts
            from src.models.requests import GetAlertsRequest

            request = GetAlertsRequest(park_code="yose")

            # Verify exception is raised
            with pytest.raises(NPSAPIError) as exc_info:
                get_alerts(request)

            assert exc_info.value.message == "API request failed"
            assert exc_info.value.status_code == 500

    def test_get_alerts_multiple_parks(self):
        """Test get_alerts with multiple park codes."""
        mock_response = {
            "total": "3",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "alert1",
                    "url": "https://www.nps.gov/yose/planyourvisit/conditions.htm",
                    "title": "Road Closure",
                    "parkCode": "yose",
                    "description": "Tioga Road is closed.",
                    "category": "Park Closure",
                    "lastIndexedDate": "2024-01-15T10:30:00Z",
                },
                {
                    "id": "alert2",
                    "url": "https://www.nps.gov/grca/planyourvisit/conditions.htm",
                    "title": "Trail Closure",
                    "parkCode": "grca",
                    "description": "Bright Angel Trail is closed.",
                    "category": "Danger",
                    "lastIndexedDate": "2024-01-14T08:00:00Z",
                },
                {
                    "id": "alert3",
                    "url": "https://www.nps.gov/grca/planyourvisit/conditions.htm",
                    "title": "Weather Advisory",
                    "parkCode": "grca",
                    "description": "High winds expected.",
                    "category": "Caution",
                    "lastIndexedDate": "2024-01-13T12:00:00Z",
                },
            ],
        }

        with patch("src.handlers.get_alerts.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_alerts.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_alerts import get_alerts
            from src.models.requests import GetAlertsRequest

            request = GetAlertsRequest(park_code="yose,grca")
            result = get_alerts(request)

            # Verify alerts are grouped correctly
            assert result["total"] == 3
            assert len(result["alertsByPark"]) == 2
            assert len(result["alertsByPark"]["yose"]) == 1
            assert len(result["alertsByPark"]["grca"]) == 2

            # Verify alert type formatting
            danger_alert = next(
                a
                for a in result["alerts"]
                if a["parkCode"] == "grca" and "Trail" in a["title"]
            )
            assert danger_alert["type"] == "Danger (significant hazard)"


class TestGetVisitorCenters:
    """Test get_visitor_centers handler."""

    def test_get_visitor_centers_success(self):
        """Test get_visitor_centers with valid parameters."""
        # Mock API response
        mock_response = {
            "total": "2",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "vc1",
                    "url": "https://www.nps.gov/yose/planyourvisit/visitorcenters.htm",
                    "name": "Valley Visitor Center",
                    "parkCode": "yose",
                    "description": "The Valley Visitor Center features exhibits...",
                    "latitude": "37.7489",
                    "longitude": "-119.5874",
                    "latLong": "lat:37.7489, long:-119.5874",
                    "directionsInfo": "Located in Yosemite Village",
                    "directionsUrl": "https://www.nps.gov/yose/planyourvisit/directions.htm",
                    "addresses": [
                        {
                            "postalCode": "95389",
                            "city": "Yosemite Valley",
                            "stateCode": "CA",
                            "line1": "9035 Village Drive",
                            "line2": "",
                            "line3": "",
                            "type": "Physical",
                        }
                    ],
                    "operatingHours": [
                        {
                            "exceptions": [],
                            "description": "Open daily",
                            "standardHours": {
                                "sunday": "9:00AM - 5:00PM",
                                "monday": "9:00AM - 5:00PM",
                                "tuesday": "9:00AM - 5:00PM",
                                "wednesday": "9:00AM - 5:00PM",
                                "thursday": "9:00AM - 5:00PM",
                                "friday": "9:00AM - 5:00PM",
                                "saturday": "9:00AM - 5:00PM",
                            },
                            "name": "Valley Visitor Center",
                        }
                    ],
                    "contacts": {
                        "phoneNumbers": [
                            {
                                "phoneNumber": "209-372-0200",
                                "description": "Main",
                                "extension": "",
                                "type": "Voice",
                            }
                        ],
                        "emailAddresses": [
                            {
                                "description": "General",
                                "emailAddress": "yose_web_manager@nps.gov",
                            }
                        ],
                    },
                },
                {
                    "id": "vc2",
                    "url": "https://www.nps.gov/yose/planyourvisit/visitorcenters.htm",
                    "name": "Tuolumne Meadows Visitor Center",
                    "parkCode": "yose",
                    "description": "The Tuolumne Meadows Visitor Center...",
                    "latitude": "37.8747",
                    "longitude": "-119.3503",
                    "latLong": "lat:37.8747, long:-119.3503",
                    "directionsInfo": "Located on Tioga Road",
                    "directionsUrl": "https://www.nps.gov/yose/planyourvisit/directions.htm",
                    "addresses": [
                        {
                            "postalCode": "95389",
                            "city": "Tuolumne Meadows",
                            "stateCode": "CA",
                            "line1": "Tioga Road",
                            "line2": "",
                            "line3": "",
                            "type": "Physical",
                        }
                    ],
                    "operatingHours": [
                        {
                            "exceptions": [],
                            "description": "Seasonal",
                            "standardHours": {
                                "sunday": "9:00AM - 5:00PM",
                                "monday": "9:00AM - 5:00PM",
                                "tuesday": "9:00AM - 5:00PM",
                                "wednesday": "9:00AM - 5:00PM",
                                "thursday": "9:00AM - 5:00PM",
                                "friday": "9:00AM - 5:00PM",
                                "saturday": "9:00AM - 5:00PM",
                            },
                            "name": "Tuolumne Meadows Visitor Center",
                        }
                    ],
                    "contacts": {
                        "phoneNumbers": [
                            {
                                "phoneNumber": "209-372-0263",
                                "description": "Main",
                                "extension": "",
                                "type": "Voice",
                            }
                        ],
                        "emailAddresses": [],
                    },
                },
            ],
        }

        with patch("src.handlers.get_visitor_centers.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_visitor_centers.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_visitor_centers import get_visitor_centers
            from src.models.requests import GetVisitorCentersRequest

            request = GetVisitorCentersRequest(park_code="yose", limit=10)
            result = get_visitor_centers(request)

            # Verify the result structure
            assert "total" in result
            assert result["total"] == 2
            assert result["limit"] == 10
            assert "visitorCenters" in result
            assert len(result["visitorCenters"]) == 2
            assert "visitorCentersByPark" in result

            # Verify visitor center formatting
            center = result["visitorCenters"][0]
            assert "name" in center
            assert center["name"] == "Valley Visitor Center"
            assert "parkCode" in center
            assert center["parkCode"] == "yose"
            assert "description" in center
            assert "location" in center
            assert "latitude" in center["location"]
            assert "longitude" in center["location"]
            assert "address" in center["location"]
            assert "operatingHours" in center
            assert "contacts" in center

            # Verify operating hours formatting
            hours = center["operatingHours"][0]
            assert "name" in hours
            assert "description" in hours
            assert "standardHours" in hours
            assert isinstance(hours["standardHours"], list)
            assert len(hours["standardHours"]) == 7  # 7 days of the week

            # Verify visitor centers are grouped by park
            assert "yose" in result["visitorCentersByPark"]
            assert len(result["visitorCentersByPark"]["yose"]) == 2

            # Verify API was called correctly
            mock_client.get_visitor_centers.assert_called_once()

    def test_get_visitor_centers_with_search(self):
        """Test get_visitor_centers with search query."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "vc1",
                    "url": "https://www.nps.gov/grca/planyourvisit/visitorcenters.htm",
                    "name": "Grand Canyon Visitor Center",
                    "parkCode": "grca",
                    "description": "The main visitor center...",
                    "latitude": "36.0544",
                    "longitude": "-112.1401",
                    "latLong": "lat:36.0544, long:-112.1401",
                    "directionsInfo": "Located near the South Rim entrance",
                    "directionsUrl": "https://www.nps.gov/grca/planyourvisit/directions.htm",
                    "addresses": [
                        {
                            "postalCode": "86023",
                            "city": "Grand Canyon",
                            "stateCode": "AZ",
                            "line1": "South Rim Drive",
                            "line2": "",
                            "line3": "",
                            "type": "Physical",
                        }
                    ],
                    "operatingHours": [
                        {
                            "exceptions": [],
                            "description": "Open year-round",
                            "standardHours": {
                                "sunday": "8:00AM - 6:00PM",
                                "monday": "8:00AM - 6:00PM",
                                "tuesday": "8:00AM - 6:00PM",
                                "wednesday": "8:00AM - 6:00PM",
                                "thursday": "8:00AM - 6:00PM",
                                "friday": "8:00AM - 6:00PM",
                                "saturday": "8:00AM - 6:00PM",
                            },
                            "name": "Grand Canyon Visitor Center",
                        }
                    ],
                    "contacts": {
                        "phoneNumbers": [
                            {
                                "phoneNumber": "928-638-7888",
                                "description": "Main",
                                "extension": "",
                                "type": "Voice",
                            }
                        ],
                        "emailAddresses": [
                            {
                                "description": "General",
                                "emailAddress": "grca_information@nps.gov",
                            }
                        ],
                    },
                }
            ],
        }

        with patch("src.handlers.get_visitor_centers.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_visitor_centers.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_visitor_centers import get_visitor_centers
            from src.models.requests import GetVisitorCentersRequest

            request = GetVisitorCentersRequest(q="grand canyon", limit=10)
            result = get_visitor_centers(request)

            # Verify the result
            assert result["total"] == 1
            assert len(result["visitorCenters"]) == 1
            assert result["visitorCenters"][0]["name"] == "Grand Canyon Visitor Center"

    def test_get_visitor_centers_empty_response(self):
        """Test get_visitor_centers with no centers found."""
        mock_response = {"total": "0", "limit": "10", "start": "0", "data": []}

        with patch("src.handlers.get_visitor_centers.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_visitor_centers.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_visitor_centers import get_visitor_centers
            from src.models.requests import GetVisitorCentersRequest

            request = GetVisitorCentersRequest(park_code="invalid")
            result = get_visitor_centers(request)

            # Verify empty result
            assert result["total"] == 0
            assert len(result["visitorCenters"]) == 0
            assert len(result["visitorCentersByPark"]) == 0

    def test_get_visitor_centers_api_error(self):
        """Test get_visitor_centers with API error."""
        with patch("src.handlers.get_visitor_centers.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_visitor_centers.side_effect = NPSAPIError(
                message="API request failed", status_code=500, error_type="api_error"
            )
            mock_get_client.return_value = mock_client

            from src.handlers.get_visitor_centers import get_visitor_centers
            from src.models.requests import GetVisitorCentersRequest

            request = GetVisitorCentersRequest(park_code="yose")

            # Verify exception is raised
            with pytest.raises(NPSAPIError) as exc_info:
                get_visitor_centers(request)

            assert exc_info.value.message == "API request failed"
            assert exc_info.value.status_code == 500

    def test_get_visitor_centers_multiple_parks(self):
        """Test get_visitor_centers with multiple park codes."""
        mock_response = {
            "total": "3",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "vc1",
                    "url": "https://www.nps.gov/yose/planyourvisit/visitorcenters.htm",
                    "name": "Valley Visitor Center",
                    "parkCode": "yose",
                    "description": "The Valley Visitor Center...",
                    "latitude": "37.7489",
                    "longitude": "-119.5874",
                    "latLong": "lat:37.7489, long:-119.5874",
                    "directionsInfo": "Located in Yosemite Village",
                    "directionsUrl": "https://www.nps.gov/yose/planyourvisit/directions.htm",
                    "addresses": [],
                    "operatingHours": [],
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                },
                {
                    "id": "vc2",
                    "url": "https://www.nps.gov/grca/planyourvisit/visitorcenters.htm",
                    "name": "Grand Canyon Visitor Center",
                    "parkCode": "grca",
                    "description": "The main visitor center...",
                    "latitude": "36.0544",
                    "longitude": "-112.1401",
                    "latLong": "lat:36.0544, long:-112.1401",
                    "directionsInfo": "Located near the South Rim entrance",
                    "directionsUrl": "https://www.nps.gov/grca/planyourvisit/directions.htm",
                    "addresses": [],
                    "operatingHours": [],
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                },
                {
                    "id": "vc3",
                    "url": "https://www.nps.gov/grca/planyourvisit/visitorcenters.htm",
                    "name": "Desert View Visitor Center",
                    "parkCode": "grca",
                    "description": "Located at Desert View...",
                    "latitude": "36.0424",
                    "longitude": "-111.8277",
                    "latLong": "lat:36.0424, long:-111.8277",
                    "directionsInfo": "Located at the east entrance",
                    "directionsUrl": "https://www.nps.gov/grca/planyourvisit/directions.htm",
                    "addresses": [],
                    "operatingHours": [],
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                },
            ],
        }

        with patch("src.handlers.get_visitor_centers.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_visitor_centers.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_visitor_centers import get_visitor_centers
            from src.models.requests import GetVisitorCentersRequest

            request = GetVisitorCentersRequest(park_code="yose,grca")
            result = get_visitor_centers(request)

            # Verify visitor centers are grouped correctly
            assert result["total"] == 3
            assert len(result["visitorCentersByPark"]) == 2
            assert len(result["visitorCentersByPark"]["yose"]) == 1
            assert len(result["visitorCentersByPark"]["grca"]) == 2


class TestFindParks:
    """Test find_parks handler."""

    def test_find_parks_success(self):
        """Test find_parks with valid parameters."""
        # Mock API response
        mock_response = {
            "total": "2",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "77E0D7F0-1942-494A-ACE2-9004D2BDC59E",
                    "url": "https://www.nps.gov/yose/index.htm",
                    "fullName": "Yosemite National Park",
                    "parkCode": "yose",
                    "description": "Not just a great valley...",
                    "latitude": "37.84883288",
                    "longitude": "-119.5571873",
                    "latLong": "lat:37.84883288, long:-119.5571873",
                    "activities": [{"id": "1", "name": "Hiking"}],
                    "topics": [{"id": "1", "name": "Geology"}],
                    "states": "CA",
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "entranceFees": [],
                    "entrancePasses": [],
                    "fees": [],
                    "directionsInfo": "You can drive to Yosemite...",
                    "directionsUrl": "http://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherInfo": "Yosemite covers nearly 1,200 square miles...",
                    "name": "Yosemite",
                    "designation": "National Park",
                },
                {
                    "id": "B39C368F-CB27-47AA-A109-3B4DE8AD8E46",
                    "url": "https://www.nps.gov/seki/index.htm",
                    "fullName": "Sequoia & Kings Canyon National Parks",
                    "parkCode": "seki",
                    "description": "This dramatic landscape...",
                    "latitude": "36.71277299",
                    "longitude": "-118.587429",
                    "latLong": "lat:36.71277299, long:-118.587429",
                    "activities": [{"id": "2", "name": "Camping"}],
                    "topics": [{"id": "2", "name": "Forests"}],
                    "states": "CA",
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "entranceFees": [],
                    "entrancePasses": [],
                    "fees": [],
                    "directionsInfo": "From Fresno...",
                    "directionsUrl": "http://www.nps.gov/seki/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherInfo": "Temperatures vary greatly...",
                    "name": "Sequoia & Kings Canyon",
                    "designation": "National Park",
                },
            ],
        }

        with patch("src.handlers.find_parks.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_parks.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.find_parks import find_parks
            from src.models.requests import FindParksRequest

            request = FindParksRequest(state_code="CA", limit=10)
            result = find_parks(request)

            # Verify the result structure
            assert "total" in result
            assert result["total"] == 2
            assert result["limit"] == 10
            assert result["start"] == 0
            assert "parks" in result
            assert len(result["parks"]) == 2

            # Verify park formatting
            park = result["parks"][0]
            assert "name" in park
            assert "code" in park
            assert "designation" in park
            assert "location" in park
            assert "description" in park

            # Verify API was called correctly
            mock_client.get_parks.assert_called_once()
            call_args = mock_client.get_parks.call_args[1]
            assert call_args["stateCode"] == "CA"
            assert call_args["limit"] == 10

    def test_find_parks_with_search_query(self):
        """Test find_parks with search query."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "77E0D7F0-1942-494A-ACE2-9004D2BDC59E",
                    "url": "https://www.nps.gov/yose/index.htm",
                    "fullName": "Yosemite National Park",
                    "parkCode": "yose",
                    "description": "Not just a great valley...",
                    "latitude": "37.84883288",
                    "longitude": "-119.5571873",
                    "latLong": "lat:37.84883288, long:-119.5571873",
                    "activities": [],
                    "topics": [],
                    "states": "CA",
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "entranceFees": [],
                    "entrancePasses": [],
                    "fees": [],
                    "directionsInfo": "You can drive to Yosemite...",
                    "directionsUrl": "http://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherInfo": "Yosemite covers nearly 1,200 square miles...",
                    "name": "Yosemite",
                    "designation": "National Park",
                }
            ],
        }

        with patch("src.handlers.find_parks.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_parks.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.find_parks import find_parks
            from src.models.requests import FindParksRequest

            request = FindParksRequest(q="yosemite", limit=10)
            result = find_parks(request)

            # Verify the result
            assert result["total"] == 1
            assert len(result["parks"]) == 1
            assert result["parks"][0]["name"] == "Yosemite National Park"

            # Verify API was called with search query
            call_args = mock_client.get_parks.call_args[1]
            assert call_args["q"] == "yosemite"

    def test_find_parks_invalid_state_code(self):
        """Test find_parks with invalid state code."""
        from src.handlers.find_parks import find_parks
        from src.models.requests import FindParksRequest

        request = FindParksRequest(state_code="XX")
        result = find_parks(request)

        # Verify error response
        assert "error" in result
        assert "Invalid state code" in result["error"]
        assert "validStateCodes" in result

    def test_find_parks_multiple_state_codes(self):
        """Test find_parks with multiple state codes."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "1",
                    "url": "https://www.nps.gov/yose/index.htm",
                    "fullName": "Yosemite National Park",
                    "parkCode": "yose",
                    "description": "Great valley...",
                    "latitude": "37.84883288",
                    "longitude": "-119.5571873",
                    "latLong": "lat:37.84883288, long:-119.5571873",
                    "activities": [],
                    "topics": [],
                    "states": "CA",
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "entranceFees": [],
                    "entrancePasses": [],
                    "fees": [],
                    "directionsInfo": "Directions...",
                    "directionsUrl": "http://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherInfo": "Weather info...",
                    "name": "Yosemite",
                    "designation": "National Park",
                }
            ],
        }

        with patch("src.handlers.find_parks.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_parks.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.find_parks import find_parks
            from src.models.requests import FindParksRequest

            request = FindParksRequest(state_code="CA,OR,WA", limit=10)
            result = find_parks(request)

            # Verify the result
            assert result["total"] == 1
            call_args = mock_client.get_parks.call_args[1]
            assert call_args["stateCode"] == "CA,OR,WA"

    def test_find_parks_empty_response(self):
        """Test find_parks with no parks found."""
        mock_response = {"total": "0", "limit": "10", "start": "0", "data": []}

        with patch("src.handlers.find_parks.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_parks.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.find_parks import find_parks
            from src.models.requests import FindParksRequest

            request = FindParksRequest(state_code="AK")
            result = find_parks(request)

            # Verify empty result
            assert result["total"] == 0
            assert len(result["parks"]) == 0

    def test_find_parks_api_error(self):
        """Test find_parks with API error."""
        with patch("src.handlers.find_parks.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_parks.side_effect = NPSAPIError(
                message="API request failed", status_code=500, error_type="api_error"
            )
            mock_get_client.return_value = mock_client

            from src.handlers.find_parks import find_parks
            from src.models.requests import FindParksRequest

            request = FindParksRequest(state_code="CA")

            # Verify exception is raised
            with pytest.raises(NPSAPIError) as exc_info:
                find_parks(request)

            assert exc_info.value.message == "API request failed"
            assert exc_info.value.status_code == 500

    def test_find_parks_with_activities(self):
        """Test find_parks with activity filter."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "1",
                    "url": "https://www.nps.gov/yose/index.htm",
                    "fullName": "Yosemite National Park",
                    "parkCode": "yose",
                    "description": "Great valley...",
                    "latitude": "37.84883288",
                    "longitude": "-119.5571873",
                    "latLong": "lat:37.84883288, long:-119.5571873",
                    "activities": [{"id": "1", "name": "Hiking"}],
                    "topics": [],
                    "states": "CA",
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "entranceFees": [],
                    "entrancePasses": [],
                    "fees": [],
                    "directionsInfo": "Directions...",
                    "directionsUrl": "http://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherInfo": "Weather info...",
                    "name": "Yosemite",
                    "designation": "National Park",
                }
            ],
        }

        with patch("src.handlers.find_parks.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_parks.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.find_parks import find_parks
            from src.models.requests import FindParksRequest

            request = FindParksRequest(activities="hiking", limit=10)
            result = find_parks(request)

            # Verify API was called with activities parameter
            call_args = mock_client.get_parks.call_args[1]
            assert call_args["activities"] == "hiking"
            assert result["total"] == 1


class TestGetCampgrounds:
    """Test get_campgrounds handler."""

    def test_get_campgrounds_success(self):
        """Test get_campgrounds with valid parameters."""
        # Mock API response
        mock_response = {
            "total": "2",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "camp1",
                    "url": "https://www.nps.gov/yose/planyourvisit/campgrounds.htm",
                    "name": "Upper Pines Campground",
                    "parkCode": "yose",
                    "description": "Upper Pines is the largest campground...",
                    "latitude": "37.7368",
                    "longitude": "-119.5571",
                    "latLong": "lat:37.7368, long:-119.5571",
                    "audioDescription": "",
                    "isPassportStampLocation": "0",
                    "passportStampLocationDescription": "",
                    "passportStampImages": [],
                    "geometryPoiId": "",
                    "reservationInfo": "Reservations required",
                    "reservationUrl": "https://www.recreation.gov",
                    "regulationsurl": "https://www.nps.gov/yose/planyourvisit/regulations.htm",
                    "regulationsOverview": "Follow all park regulations",
                    "amenities": {
                        "trashRecyclingCollection": "Yes",
                        "toilets": ["Flush Toilets"],
                        "internetConnectivity": "No",
                        "showers": ["None"],
                        "cellPhoneReception": "No",
                        "laundry": "No",
                        "amphitheater": "No",
                        "dumpStation": "No",
                        "campStore": "Yes",
                        "staffOrVolunteerHostOnsite": "Yes",
                        "potableWater": ["Yes"],
                        "iceAvailableForSale": "No",
                        "firewoodForSale": "Yes",
                        "foodStorageLockers": "Yes",
                    },
                    "contacts": {
                        "phoneNumbers": [
                            {
                                "phoneNumber": "209-372-8502",
                                "description": "Campground",
                                "extension": "",
                                "type": "Voice",
                            }
                        ],
                        "emailAddresses": [],
                    },
                    "fees": [
                        {
                            "cost": "26.00",
                            "description": "Per night",
                            "title": "Campsite Fee",
                        }
                    ],
                    "directionsOverview": "Located in Yosemite Valley",
                    "directionsUrl": "https://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherOverview": "Weather varies by season",
                    "numberOfSitesReservable": "238",
                    "numberOfSitesFirstComeFirstServe": "0",
                    "campsites": {
                        "totalSites": "238",
                        "group": "0",
                        "horse": "0",
                        "tentOnly": "35",
                        "electricalHookups": "0",
                        "rvOnly": "0",
                        "walkBoatTo": "0",
                        "other": "203",
                    },
                    "accessibility": {
                        "wheelchairAccess": "Partial",
                        "internetInfo": "",
                        "cellPhoneInfo": "Limited cell service",
                        "fireStovePolicy": "Allowed in designated areas",
                        "rvAllowed": "1",
                        "rvInfo": "RVs up to 35 feet",
                        "rvMaxLength": "35",
                        "additionalInfo": "",
                        "trailerMaxLength": "35",
                        "adaInfo": "ADA accessible sites available",
                        "trailerAllowed": "1",
                        "accessRoads": ["Paved Roads"],
                        "classifications": ["Developed Campground"],
                    },
                },
                {
                    "id": "camp2",
                    "url": "https://www.nps.gov/yose/planyourvisit/campgrounds.htm",
                    "name": "Lower Pines Campground",
                    "parkCode": "yose",
                    "description": "Lower Pines is located in Yosemite Valley...",
                    "latitude": "37.7368",
                    "longitude": "-119.5571",
                    "latLong": "lat:37.7368, long:-119.5571",
                    "audioDescription": "",
                    "isPassportStampLocation": "0",
                    "passportStampLocationDescription": "",
                    "passportStampImages": [],
                    "geometryPoiId": "",
                    "reservationInfo": "Reservations required",
                    "reservationUrl": "https://www.recreation.gov",
                    "regulationsurl": "https://www.nps.gov/yose/planyourvisit/regulations.htm",
                    "regulationsOverview": "Follow all park regulations",
                    "amenities": {
                        "trashRecyclingCollection": "Yes",
                        "toilets": ["Flush Toilets"],
                        "internetConnectivity": "No",
                        "showers": ["None"],
                        "cellPhoneReception": "No",
                        "laundry": "No",
                        "amphitheater": "No",
                        "dumpStation": "No",
                        "campStore": "Yes",
                        "staffOrVolunteerHostOnsite": "Yes",
                        "potableWater": ["Yes"],
                        "iceAvailableForSale": "No",
                        "firewoodForSale": "Yes",
                        "foodStorageLockers": "Yes",
                    },
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "fees": [],
                    "directionsOverview": "Located in Yosemite Valley",
                    "directionsUrl": "https://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherOverview": "Weather varies by season",
                    "numberOfSitesReservable": "60",
                    "numberOfSitesFirstComeFirstServe": "0",
                    "campsites": {
                        "totalSites": "60",
                        "group": "0",
                        "horse": "0",
                        "tentOnly": "0",
                        "electricalHookups": "0",
                        "rvOnly": "0",
                        "walkBoatTo": "0",
                        "other": "60",
                    },
                    "accessibility": {
                        "wheelchairAccess": "Partial",
                        "internetInfo": "",
                        "cellPhoneInfo": "Limited cell service",
                        "fireStovePolicy": "Allowed in designated areas",
                        "rvAllowed": "1",
                        "rvInfo": "RVs up to 40 feet",
                        "rvMaxLength": "40",
                        "additionalInfo": "",
                        "trailerMaxLength": "40",
                        "adaInfo": "ADA accessible sites available",
                        "trailerAllowed": "1",
                        "accessRoads": ["Paved Roads"],
                        "classifications": ["Developed Campground"],
                    },
                },
            ],
        }

        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_campgrounds import get_campgrounds
            from src.models.requests import GetCampgroundsRequest

            request = GetCampgroundsRequest(park_code="yose", limit=10)
            result = get_campgrounds(request)

            # Verify the result structure
            assert "total" in result
            assert result["total"] == 2
            assert result["limit"] == 10
            assert "campgrounds" in result
            assert len(result["campgrounds"]) == 2
            assert "campgroundsByPark" in result

            # Verify campground formatting
            campground = result["campgrounds"][0]
            assert "name" in campground
            assert campground["name"] == "Upper Pines Campground"
            assert "parkCode" in campground
            assert campground["parkCode"] == "yose"
            assert "description" in campground

            # Verify campgrounds are grouped by park
            assert "yose" in result["campgroundsByPark"]
            assert len(result["campgroundsByPark"]["yose"]) == 2

            # Verify API was called correctly
            mock_client.get_campgrounds.assert_called_once()

    def test_get_campgrounds_with_search(self):
        """Test get_campgrounds with search query."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "camp1",
                    "url": "https://www.nps.gov/grca/planyourvisit/campgrounds.htm",
                    "name": "Mather Campground",
                    "parkCode": "grca",
                    "description": "Mather Campground is located on the South Rim...",
                    "latitude": "36.0544",
                    "longitude": "-112.1401",
                    "latLong": "lat:36.0544, long:-112.1401",
                    "audioDescription": "",
                    "isPassportStampLocation": False,
                    "passportStampLocationDescription": "",
                    "passportStampImages": [],
                    "geometryPoiId": "",
                    "reservationInfo": "Reservations recommended",
                    "reservationUrl": "https://www.recreation.gov",
                    "regulationsurl": "https://www.nps.gov/grca/planyourvisit/regulations.htm",
                    "regulationsOverview": "Follow all park regulations",
                    "amenities": {
                        "trashRecyclingCollection": True,
                        "toilets": ["Flush Toilets"],
                        "internetConnectivity": False,
                        "showers": ["None"],
                        "cellPhoneReception": False,
                        "laundry": True,
                        "amphitheater": False,
                        "dumpStation": True,
                        "campStore": True,
                        "staffOrVolunteerHostOnsite": True,
                        "potableWater": ["Yes"],
                        "iceAvailableForSale": True,
                        "firewoodForSale": True,
                        "foodStorageLockers": False,
                    },
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "fees": [],
                    "directionsOverview": "Located on the South Rim",
                    "directionsUrl": "https://www.nps.gov/grca/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherOverview": "Weather varies by season",
                    "numberOfSitesReservable": "277",
                    "numberOfSitesFirstComeFirstServe": "50",
                    "campsites": {
                        "totalSites": "327",
                        "group": "0",
                        "horse": "0",
                        "tentOnly": "0",
                        "electricalHookups": "0",
                        "rvOnly": "0",
                        "walkBoatTo": "0",
                        "other": "327",
                    },
                    "accessibility": {
                        "wheelchairAccess": "Yes",
                        "internetInfo": "",
                        "cellPhoneInfo": "Limited cell service",
                        "fireStovePolicy": "Allowed in designated areas",
                        "rvAllowed": True,
                        "rvInfo": "RVs up to 30 feet",
                        "rvMaxLength": "30",
                        "additionalInfo": "",
                        "trailerMaxLength": "30",
                        "adaInfo": "ADA accessible sites available",
                        "trailerAllowed": True,
                        "accessRoads": ["Paved Roads"],
                        "classifications": ["Developed Campground"],
                    },
                }
            ],
        }

        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_campgrounds import get_campgrounds
            from src.models.requests import GetCampgroundsRequest

            request = GetCampgroundsRequest(q="mather", limit=10)
            result = get_campgrounds(request)

            # Verify the result
            assert result["total"] == 1
            assert len(result["campgrounds"]) == 1
            assert result["campgrounds"][0]["name"] == "Mather Campground"

    def test_get_campgrounds_empty_response(self):
        """Test get_campgrounds with no campgrounds found."""
        mock_response = {"total": "0", "limit": "10", "start": "0", "data": []}

        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_campgrounds import get_campgrounds
            from src.models.requests import GetCampgroundsRequest

            request = GetCampgroundsRequest(park_code="invalid")
            result = get_campgrounds(request)

            # Verify empty result
            assert result["total"] == 0
            assert len(result["campgrounds"]) == 0
            assert len(result["campgroundsByPark"]) == 0

    def test_get_campgrounds_api_error(self):
        """Test get_campgrounds with API error."""
        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.side_effect = NPSAPIError(
                message="API request failed", status_code=500, error_type="api_error"
            )
            mock_get_client.return_value = mock_client

            from src.handlers.get_campgrounds import get_campgrounds
            from src.models.requests import GetCampgroundsRequest

            request = GetCampgroundsRequest(park_code="yose")

            # Verify exception is raised
            with pytest.raises(NPSAPIError) as exc_info:
                get_campgrounds(request)

            assert exc_info.value.message == "API request failed"
            assert exc_info.value.status_code == 500

    def test_get_campgrounds_multiple_parks(self):
        """Test get_campgrounds with multiple park codes."""
        mock_response = {
            "total": "3",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "camp1",
                    "url": "https://www.nps.gov/yose/planyourvisit/campgrounds.htm",
                    "name": "Upper Pines Campground",
                    "parkCode": "yose",
                    "description": "Upper Pines...",
                    "latitude": "37.7368",
                    "longitude": "-119.5571",
                    "latLong": "lat:37.7368, long:-119.5571",
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
                        "trashRecyclingCollection": True,
                        "toilets": [],
                        "internetConnectivity": False,
                        "showers": [],
                        "cellPhoneReception": False,
                        "laundry": False,
                        "amphitheater": False,
                        "dumpStation": False,
                        "campStore": False,
                        "staffOrVolunteerHostOnsite": False,
                        "potableWater": [],
                        "iceAvailableForSale": False,
                        "firewoodForSale": False,
                        "foodStorageLockers": False,
                    },
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "fees": [],
                    "directionsOverview": "",
                    "directionsUrl": "",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherOverview": "",
                    "numberOfSitesReservable": "238",
                    "numberOfSitesFirstComeFirstServe": "0",
                    "campsites": {
                        "totalSites": "238",
                        "group": "0",
                        "horse": "0",
                        "tentOnly": "0",
                        "electricalHookups": "0",
                        "rvOnly": "0",
                        "walkBoatTo": "0",
                        "other": "238",
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
                },
                {
                    "id": "camp2",
                    "url": "https://www.nps.gov/grca/planyourvisit/campgrounds.htm",
                    "name": "Mather Campground",
                    "parkCode": "grca",
                    "description": "Mather...",
                    "latitude": "36.0544",
                    "longitude": "-112.1401",
                    "latLong": "lat:36.0544, long:-112.1401",
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
                        "trashRecyclingCollection": True,
                        "toilets": [],
                        "internetConnectivity": False,
                        "showers": [],
                        "cellPhoneReception": False,
                        "laundry": False,
                        "amphitheater": False,
                        "dumpStation": False,
                        "campStore": False,
                        "staffOrVolunteerHostOnsite": False,
                        "potableWater": [],
                        "iceAvailableForSale": False,
                        "firewoodForSale": False,
                        "foodStorageLockers": False,
                    },
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "fees": [],
                    "directionsOverview": "",
                    "directionsUrl": "",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherOverview": "",
                    "numberOfSitesReservable": "277",
                    "numberOfSitesFirstComeFirstServe": "50",
                    "campsites": {
                        "totalSites": "327",
                        "group": "0",
                        "horse": "0",
                        "tentOnly": "0",
                        "electricalHookups": "0",
                        "rvOnly": "0",
                        "walkBoatTo": "0",
                        "other": "327",
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
                },
                {
                    "id": "camp3",
                    "url": "https://www.nps.gov/grca/planyourvisit/campgrounds.htm",
                    "name": "Desert View Campground",
                    "parkCode": "grca",
                    "description": "Desert View...",
                    "latitude": "36.0424",
                    "longitude": "-111.8277",
                    "latLong": "lat:36.0424, long:-111.8277",
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
                        "trashRecyclingCollection": True,
                        "toilets": [],
                        "internetConnectivity": False,
                        "showers": [],
                        "cellPhoneReception": False,
                        "laundry": False,
                        "amphitheater": False,
                        "dumpStation": False,
                        "campStore": False,
                        "staffOrVolunteerHostOnsite": False,
                        "potableWater": [],
                        "iceAvailableForSale": False,
                        "firewoodForSale": False,
                        "foodStorageLockers": False,
                    },
                    "contacts": {"phoneNumbers": [], "emailAddresses": []},
                    "fees": [],
                    "directionsOverview": "",
                    "directionsUrl": "",
                    "operatingHours": [],
                    "addresses": [],
                    "images": [],
                    "weatherOverview": "",
                    "numberOfSitesReservable": "50",
                    "numberOfSitesFirstComeFirstServe": "0",
                    "campsites": {
                        "totalSites": "50",
                        "group": "0",
                        "horse": "0",
                        "tentOnly": "0",
                        "electricalHookups": "0",
                        "rvOnly": "0",
                        "walkBoatTo": "0",
                        "other": "50",
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
                },
            ],
        }

        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_campgrounds import get_campgrounds
            from src.models.requests import GetCampgroundsRequest

            request = GetCampgroundsRequest(park_code="yose,grca")
            result = get_campgrounds(request)

            # Verify campgrounds are grouped correctly
            assert result["total"] == 3
            assert len(result["campgroundsByPark"]) == 2
            assert len(result["campgroundsByPark"]["yose"]) == 1
            assert len(result["campgroundsByPark"]["grca"]) == 2


class TestGetEvents:
    """Test get_events handler."""

    def test_get_events_success(self):
        """Test get_events with valid parameters."""
        # Mock API response
        mock_response = {
            "total": "2",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "url": "https://www.nps.gov/yose/planyourvisit/events.htm",
                    "title": "Ranger-Led Hike",
                    "parkCode": "yose",
                    "description": "Join a ranger for a guided hike...",
                    "location": "Valley Visitor Center",
                    "latitude": "37.7489",
                    "longitude": "-119.5874",
                    "latLong": "lat:37.7489, long:-119.5874",
                    "category": "Guided Tours",
                    "tags": ["hiking", "ranger program"],
                    "dateStart": "2024-06-15",
                    "dateEnd": "2024-06-15",
                    "timeStart": "09:00:00",
                    "timeEnd": "12:00:00",
                    "durationHours": "3",
                    "durationMinutes": "0",
                    "isRecurring": "false",
                    "isAllDay": "false",
                    "isFree": "true",
                    "feeInfo": "",
                    "isRegResRequired": "false",
                    "regResInfo": "",
                    "regResUrl": "",
                    "contactName": "Yosemite Visitor Services",
                    "contactTelephoneNumber": "209-372-0200",
                    "contactEmailAddress": "yose_web_manager@nps.gov",
                    "types": ["Event"],
                    "images": [],
                    "infoUrl": "https://www.nps.gov/yose/planyourvisit/events.htm",
                    "portalName": "",
                },
                {
                    "id": "event2",
                    "url": "https://www.nps.gov/yose/planyourvisit/events.htm",
                    "title": "Evening Program",
                    "parkCode": "yose",
                    "description": "Learn about Yosemite's wildlife...",
                    "location": "Curry Village Amphitheater",
                    "latitude": "37.7368",
                    "longitude": "-119.5571",
                    "latLong": "lat:37.7368, long:-119.5571",
                    "category": "Evening Programs",
                    "tags": ["wildlife", "ranger program"],
                    "dateStart": "2024-06-15",
                    "dateEnd": "2024-06-15",
                    "timeStart": "20:00:00",
                    "timeEnd": "21:00:00",
                    "durationHours": "1",
                    "durationMinutes": "0",
                    "isRecurring": "true",
                    "isAllDay": "false",
                    "isFree": "true",
                    "feeInfo": "",
                    "isRegResRequired": "false",
                    "regResInfo": "",
                    "regResUrl": "",
                    "contactName": "Yosemite Visitor Services",
                    "contactTelephoneNumber": "209-372-0200",
                    "contactEmailAddress": "yose_web_manager@nps.gov",
                    "types": ["Event"],
                    "images": [],
                    "infoUrl": "https://www.nps.gov/yose/planyourvisit/events.htm",
                    "portalName": "",
                },
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_events import get_events
            from src.models.requests import GetEventsRequest

            request = GetEventsRequest(park_code="yose", limit=10)
            result = get_events(request)

            # Verify the result structure
            assert "total" in result
            assert result["total"] == 2
            assert result["limit"] == 10
            assert "events" in result
            assert len(result["events"]) == 2
            assert "eventsByPark" in result

            # Verify event formatting
            event = result["events"][0]
            assert "title" in event
            assert event["title"] == "Ranger-Led Hike"
            assert "parkCode" in event
            assert event["parkCode"] == "yose"
            assert "description" in event
            assert "location" in event

            # Verify events are grouped by park
            assert "yose" in result["eventsByPark"]
            assert len(result["eventsByPark"]["yose"]) == 2

            # Verify API was called correctly
            mock_client.get_events.assert_called_once()

    def test_get_events_with_date_range(self):
        """Test get_events with date range filter."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "url": "https://www.nps.gov/grca/planyourvisit/events.htm",
                    "title": "Summer Solstice Celebration",
                    "parkCode": "grca",
                    "description": "Celebrate the summer solstice...",
                    "location": "South Rim",
                    "latitude": "36.0544",
                    "longitude": "-112.1401",
                    "latLong": "lat:36.0544, long:-112.1401",
                    "category": "Special Events",
                    "tags": ["celebration", "summer"],
                    "dateStart": "2024-06-21",
                    "dateEnd": "2024-06-21",
                    "timeStart": "06:00:00",
                    "timeEnd": "08:00:00",
                    "durationHours": "2",
                    "durationMinutes": "0",
                    "isRecurring": "false",
                    "isAllDay": "false",
                    "isFree": "true",
                    "feeInfo": "",
                    "isRegResRequired": "false",
                    "regResInfo": "",
                    "regResUrl": "",
                    "contactName": "Grand Canyon Visitor Services",
                    "contactTelephoneNumber": "928-638-7888",
                    "contactEmailAddress": "grca_information@nps.gov",
                    "types": ["Event"],
                    "images": [],
                    "infoUrl": "https://www.nps.gov/grca/planyourvisit/events.htm",
                    "portalName": "",
                }
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_events import get_events
            from src.models.requests import GetEventsRequest

            request = GetEventsRequest(
                park_code="grca",
                date_start="2024-06-01",
                date_end="2024-06-30",
                limit=10,
            )
            result = get_events(request)

            # Verify the result
            assert result["total"] == 1
            assert len(result["events"]) == 1
            assert result["events"][0]["title"] == "Summer Solstice Celebration"

            # Verify API was called with date parameters
            call_args = mock_client.get_events.call_args[1]
            assert call_args["dateStart"] == "2024-06-01"
            assert call_args["dateEnd"] == "2024-06-30"

    def test_get_events_with_search(self):
        """Test get_events with search query."""
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "url": "https://www.nps.gov/yose/planyourvisit/events.htm",
                    "title": "Ranger-Led Hike",
                    "parkCode": "yose",
                    "description": "Join a ranger for a guided hike...",
                    "location": "Valley Visitor Center",
                    "latitude": "37.7489",
                    "longitude": "-119.5874",
                    "latLong": "lat:37.7489, long:-119.5874",
                    "category": "Guided Tours",
                    "tags": ["hiking", "ranger program"],
                    "dateStart": "2024-06-15",
                    "dateEnd": "2024-06-15",
                    "timeStart": "09:00:00",
                    "timeEnd": "12:00:00",
                    "durationHours": "3",
                    "durationMinutes": "0",
                    "isRecurring": "false",
                    "isAllDay": "false",
                    "isFree": "true",
                    "feeInfo": "",
                    "isRegResRequired": "false",
                    "regResInfo": "",
                    "regResUrl": "",
                    "contactName": "Yosemite Visitor Services",
                    "contactTelephoneNumber": "209-372-0200",
                    "contactEmailAddress": "yose_web_manager@nps.gov",
                    "types": ["Event"],
                    "images": [],
                    "infoUrl": "https://www.nps.gov/yose/planyourvisit/events.htm",
                    "portalName": "",
                }
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_events import get_events
            from src.models.requests import GetEventsRequest

            request = GetEventsRequest(q="ranger", limit=10)
            result = get_events(request)

            # Verify the result
            assert result["total"] == 1
            assert len(result["events"]) == 1
            assert "Ranger" in result["events"][0]["title"]

    def test_get_events_empty_response(self):
        """Test get_events with no events found."""
        mock_response = {"total": "0", "limit": "10", "start": "0", "data": []}

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_events import get_events
            from src.models.requests import GetEventsRequest

            request = GetEventsRequest(park_code="invalid")
            result = get_events(request)

            # Verify empty result
            assert result["total"] == 0
            assert len(result["events"]) == 0
            assert len(result["eventsByPark"]) == 0

    def test_get_events_api_error(self):
        """Test get_events with API error."""
        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.side_effect = NPSAPIError(
                message="API request failed", status_code=500, error_type="api_error"
            )
            mock_get_client.return_value = mock_client

            from src.handlers.get_events import get_events
            from src.models.requests import GetEventsRequest

            request = GetEventsRequest(park_code="yose")

            # Verify exception is raised
            with pytest.raises(NPSAPIError) as exc_info:
                get_events(request)

            assert exc_info.value.message == "API request failed"
            assert exc_info.value.status_code == 500

    def test_get_events_multiple_parks(self):
        """Test get_events with multiple park codes."""
        mock_response = {
            "total": "3",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "url": "https://www.nps.gov/yose/planyourvisit/events.htm",
                    "title": "Ranger-Led Hike",
                    "parkCode": "yose",
                    "description": "Join a ranger...",
                    "location": "Valley Visitor Center",
                    "latitude": "37.7489",
                    "longitude": "-119.5874",
                    "latLong": "lat:37.7489, long:-119.5874",
                    "category": "Guided Tours",
                    "tags": [],
                    "dateStart": "2024-06-15",
                    "dateEnd": "2024-06-15",
                    "timeStart": "09:00:00",
                    "timeEnd": "12:00:00",
                    "durationHours": "3",
                    "durationMinutes": "0",
                    "isRecurring": "false",
                    "isAllDay": "false",
                    "isFree": "true",
                    "feeInfo": "",
                    "isRegResRequired": "false",
                    "regResInfo": "",
                    "regResUrl": "",
                    "contactName": "",
                    "contactTelephoneNumber": "",
                    "contactEmailAddress": "",
                    "types": [],
                    "images": [],
                    "infoUrl": "",
                    "portalName": "",
                },
                {
                    "id": "event2",
                    "url": "https://www.nps.gov/grca/planyourvisit/events.htm",
                    "title": "Sunrise Tour",
                    "parkCode": "grca",
                    "description": "Watch the sunrise...",
                    "location": "South Rim",
                    "latitude": "36.0544",
                    "longitude": "-112.1401",
                    "latLong": "lat:36.0544, long:-112.1401",
                    "category": "Guided Tours",
                    "tags": [],
                    "dateStart": "2024-06-16",
                    "dateEnd": "2024-06-16",
                    "timeStart": "05:30:00",
                    "timeEnd": "07:00:00",
                    "durationHours": "1",
                    "durationMinutes": "30",
                    "isRecurring": "true",
                    "isAllDay": "false",
                    "isFree": "true",
                    "feeInfo": "",
                    "isRegResRequired": "false",
                    "regResInfo": "",
                    "regResUrl": "",
                    "contactName": "",
                    "contactTelephoneNumber": "",
                    "contactEmailAddress": "",
                    "types": [],
                    "images": [],
                    "infoUrl": "",
                    "portalName": "",
                },
                {
                    "id": "event3",
                    "url": "https://www.nps.gov/grca/planyourvisit/events.htm",
                    "title": "Evening Program",
                    "parkCode": "grca",
                    "description": "Learn about the canyon...",
                    "location": "Mather Amphitheater",
                    "latitude": "36.0544",
                    "longitude": "-112.1401",
                    "latLong": "lat:36.0544, long:-112.1401",
                    "category": "Evening Programs",
                    "tags": [],
                    "dateStart": "2024-06-16",
                    "dateEnd": "2024-06-16",
                    "timeStart": "20:00:00",
                    "timeEnd": "21:00:00",
                    "durationHours": "1",
                    "durationMinutes": "0",
                    "isRecurring": "true",
                    "isAllDay": "false",
                    "isFree": "true",
                    "feeInfo": "",
                    "isRegResRequired": "false",
                    "regResInfo": "",
                    "regResUrl": "",
                    "contactName": "",
                    "contactTelephoneNumber": "",
                    "contactEmailAddress": "",
                    "types": [],
                    "images": [],
                    "infoUrl": "",
                    "portalName": "",
                },
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            from src.handlers.get_events import get_events
            from src.models.requests import GetEventsRequest

            request = GetEventsRequest(park_code="yose,grca")
            result = get_events(request)

            # Verify events are grouped correctly
            assert result["total"] == 3
            assert len(result["eventsByPark"]) == 2
            assert len(result["eventsByPark"]["yose"]) == 1
            assert len(result["eventsByPark"]["grca"]) == 2
