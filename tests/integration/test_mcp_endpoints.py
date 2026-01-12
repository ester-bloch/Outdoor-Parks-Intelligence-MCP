"""Integration tests for MCP endpoints with real API structure.

Tests getCampgrounds and getEvents endpoints with realistic NPS API responses
to verify no validation errors occur.
Requirements: 5.3, 5.4
"""

from unittest.mock import Mock, patch

from src.handlers.get_campgrounds import get_campgrounds
from src.handlers.get_events import get_events
from src.models.requests import GetCampgroundsRequest, GetEventsRequest


class TestGetCampgroundsIntegration:
    """Integration tests for getCampgrounds endpoint."""

    def test_get_campgrounds_with_real_api_structure(self):
        """Test getCampgrounds with realistic NPS API response structure.

        Validates: Requirements 5.3
        """
        # Mock response with realistic NPS API structure including string booleans
        mock_response = {
            "total": "2",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "campground1",
                    "url": "https://www.nps.gov/yose/planyourvisit/camp1.htm",
                    "name": "Upper Pines Campground",
                    "parkCode": "yose",
                    "description": "Upper Pines Campground is located in Yosemite Valley.",
                    "latitude": "37.7365",
                    "longitude": "-119.5571",
                    "latLong": "lat:37.7365, long:-119.5571",
                    "audioDescription": "",
                    "isPassportStampLocation": False,
                    "passportStampLocationDescription": "",
                    "passportStampImages": [],
                    "geometryPoiId": "",
                    "reservationInfo": "Reservations required",
                    "reservationUrl": "https://www.recreation.gov",
                    "regulationsurl": "",
                    "regulationsOverview": "",
                    "amenities": {
                        "trashRecyclingCollection": "Yes",  # String boolean
                        "toilets": ["Flush Toilets"],
                        "internetConnectivity": False,
                        "showers": [],
                        "cellPhoneReception": "No",  # String boolean
                        "laundry": False,
                        "amphitheater": True,
                        "dumpStation": True,
                        "campStore": False,
                        "staffOrVolunteerHostOnsite": "Yes",  # String boolean
                        "potableWater": ["Yes"],
                        "iceAvailableForSale": False,
                        "firewoodForSale": True,
                        "foodStorageLockers": "Unknown",  # String boolean
                    },
                    "contacts": {
                        "phoneNumbers": [
                            {
                                "phoneNumber": "209-372-0200",
                                "description": "Main",
                                "extension": "",
                                "type": "Voice",
                            }
                        ],
                        "emailAddresses": [],
                    },
                    "fees": [],
                    "directionsOverview": "Located in Yosemite Valley",
                    "directionsUrl": "https://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
                    "weatherOverview": "Weather varies by season",
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
                        "other": "0",
                    },
                    "accessibility": {
                        "wheelchairAccess": "Yes",
                        "internetInfo": "No internet",
                        "cellPhoneInfo": "Limited reception",
                        "fireStovePolicy": "Allowed in designated areas",
                        "rvAllowed": True,
                        "rvInfo": "RVs up to 35 feet",
                        "rvMaxLength": "35",
                        "additionalInfo": "",
                        "trailerMaxLength": "35",
                        "adaInfo": "ADA accessible sites available",
                        "trailerAllowed": True,
                        "accessRoads": ["Paved"],
                        "classifications": ["Developed Campground"],
                    },
                },
                {
                    "id": "campground2",
                    "url": "https://www.nps.gov/yose/planyourvisit/camp2.htm",
                    "name": "Lower Pines Campground",
                    "parkCode": "yose",
                    "description": "Lower Pines Campground is located in Yosemite Valley.",
                    "latitude": "37.7365",
                    "longitude": "-119.5571",
                    "latLong": "lat:37.7365, long:-119.5571",
                    "audioDescription": "",
                    "isPassportStampLocation": False,
                    "passportStampLocationDescription": "",
                    "passportStampImages": [],
                    "geometryPoiId": "",
                    "reservationInfo": "Reservations required",
                    "reservationUrl": "https://www.recreation.gov",
                    "regulationsurl": "",
                    "regulationsOverview": "",
                    "amenities": {
                        "trashRecyclingCollection": "true",  # String boolean variant
                        "toilets": ["Flush Toilets"],
                        "internetConnectivity": False,
                        "showers": [],
                        "cellPhoneReception": "false",  # String boolean variant
                        "laundry": False,
                        "amphitheater": False,
                        "dumpStation": True,
                        "campStore": False,
                        "staffOrVolunteerHostOnsite": "1",  # String boolean variant
                        "potableWater": ["Yes"],
                        "iceAvailableForSale": False,
                        "firewoodForSale": True,
                        "foodStorageLockers": "N/A",  # String boolean variant
                    },
                    "contacts": {
                        "phoneNumbers": [],
                        "emailAddresses": [],
                    },
                    "fees": [],
                    "directionsOverview": "Located in Yosemite Valley",
                    "directionsUrl": "https://www.nps.gov/yose/planyourvisit/directions.htm",
                    "operatingHours": [],
                    "addresses": [],
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
                        "other": "0",
                    },
                    "accessibility": {
                        "wheelchairAccess": "Yes",
                        "internetInfo": "No internet",
                        "cellPhoneInfo": "Limited reception",
                        "fireStovePolicy": "Allowed in designated areas",
                        "rvAllowed": True,
                        "rvInfo": "RVs up to 40 feet",
                        "rvMaxLength": "40",
                        "additionalInfo": "",
                        "trailerMaxLength": "40",
                        "adaInfo": "ADA accessible sites available",
                        "trailerAllowed": True,
                        "accessRoads": ["Paved"],
                        "classifications": ["Developed Campground"],
                    },
                },
            ],
        }

        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetCampgroundsRequest(park_code="yose", limit=10)
            result = get_campgrounds(request)

            # Verify response structure
            assert isinstance(result, dict)
            assert "total" in result
            assert "campgrounds" in result
            assert "campgroundsByPark" in result
            assert result["total"] == 2
            assert len(result["campgrounds"]) == 2

            # Verify no validation errors occurred
            assert len(result["campgrounds"]) == 2

            # Verify campground data
            campground1 = result["campgrounds"][0]
            assert campground1["name"] == "Upper Pines Campground"
            assert campground1["parkCode"] == "yose"

            # Verify campgrounds grouped by park
            assert "yose" in result["campgroundsByPark"]
            assert len(result["campgroundsByPark"]["yose"]) == 2

    def test_get_campgrounds_with_parkcode_parameter(self):
        """Test getCampgrounds with parkCode parameter (e.g., 'yose').

        Validates: Requirements 5.3
        """
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "campground1",
                    "url": "https://www.nps.gov/yose/planyourvisit/camp1.htm",
                    "name": "Upper Pines Campground",
                    "parkCode": "yose",
                    "description": "Upper Pines Campground is located in Yosemite Valley.",
                    "latitude": "37.7365",
                    "longitude": "-119.5571",
                    "latLong": "lat:37.7365, long:-119.5571",
                    "audioDescription": "",
                    "isPassportStampLocation": False,
                    "passportStampLocationDescription": "",
                    "passportStampImages": [],
                    "geometryPoiId": "",
                    "reservationInfo": "Reservations required",
                    "reservationUrl": "https://www.recreation.gov",
                    "regulationsurl": "",
                    "regulationsOverview": "",
                    "amenities": {
                        "trashRecyclingCollection": "YES",  # Uppercase variant
                        "toilets": [],
                        "internetConnectivity": False,
                        "showers": [],
                        "cellPhoneReception": "NO",  # Uppercase variant
                        "laundry": False,
                        "amphitheater": False,
                        "dumpStation": False,
                        "campStore": False,
                        "staffOrVolunteerHostOnsite": "",  # Empty string
                        "potableWater": [],
                        "iceAvailableForSale": False,
                        "firewoodForSale": False,
                        "foodStorageLockers": "Not Available",  # String variant
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
                        "rvMaxLength": "0",
                        "additionalInfo": "",
                        "trailerMaxLength": "0",
                        "adaInfo": "",
                        "trailerAllowed": False,
                        "accessRoads": [],
                        "classifications": [],
                    },
                }
            ],
        }

        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetCampgroundsRequest(park_code="yose", limit=10)
            result = get_campgrounds(request)

            # Verify response structure
            assert result["total"] == 1
            assert len(result["campgrounds"]) == 1
            assert result["campgrounds"][0]["parkCode"] == "yose"

    def test_get_campgrounds_no_validation_errors(self):
        """Test that getCampgrounds handles all boolean string variants without errors.

        Validates: Requirements 5.3
        """
        # Test with various boolean string formats
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "test",
                    "url": "https://test.com",
                    "name": "Test Campground",
                    "parkCode": "test",
                    "description": "Test",
                    "latitude": "0",
                    "longitude": "0",
                    "latLong": "lat:0, long:0",
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
                        "trashRecyclingCollection": "0",  # String "0"
                        "toilets": [],
                        "internetConnectivity": False,
                        "showers": [],
                        "cellPhoneReception": True,  # Already boolean
                        "laundry": False,
                        "amphitheater": False,
                        "dumpStation": False,
                        "campStore": False,
                        "staffOrVolunteerHostOnsite": None,  # None value
                        "potableWater": [],
                        "iceAvailableForSale": False,
                        "firewoodForSale": False,
                        "foodStorageLockers": "yes",  # Lowercase
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
                        "rvMaxLength": "0",
                        "additionalInfo": "",
                        "trailerMaxLength": "0",
                        "adaInfo": "",
                        "trailerAllowed": False,
                        "accessRoads": [],
                        "classifications": [],
                    },
                }
            ],
        }

        with patch("src.handlers.get_campgrounds.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_campgrounds.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetCampgroundsRequest(park_code="test", limit=10)
            # Should not raise any validation errors
            result = get_campgrounds(request)

            assert result["total"] == 1
            assert len(result["campgrounds"]) == 1


class TestGetEventsIntegration:
    """Integration tests for getEvents endpoint."""

    def test_get_events_with_real_api_structure(self):
        """Test getEvents with realistic NPS API response structure.

        Validates: Requirements 5.4
        """
        # Mock response with realistic NPS API structure including string booleans
        mock_response = {
            "total": "2",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "title": "Ranger-Led Hike",
                    "url": "https://www.nps.gov/yose/planyourvisit/event1.htm",
                    "parkFullName": "Yosemite National Park",
                    "description": "Join a ranger for a guided hike.",
                    "latitude": "37.7489",
                    "longitude": "-119.5874",
                    "category": "Guided Tours",
                    "subcategory": "Hiking",
                    "location": "Valley Visitor Center",
                    "tags": ["hiking", "ranger"],
                    "recurrenceDateStart": "2024-01-01",
                    "recurrenceDateEnd": "2024-12-31",
                    "times": [
                        {
                            "timeStart": "09:00",
                            "timeEnd": "11:00",
                            "sunriseTimeStart": "No",  # String boolean
                            "sunsetTimeEnd": "false",  # String boolean
                        }
                    ],
                    "dates": ["2024-01-15"],
                    "dateStart": "2024-01-15",
                    "dateEnd": "2024-01-15",
                    "regresurl": "",
                    "contactEmailAddress": "yose_info@nps.gov",
                    "contactTelephoneNumber": "209-372-0200",
                    "feeInfo": "Free",
                    "isRecurring": "Yes",  # String boolean
                    "isAllDay": "No",  # String boolean
                    "siteCode": "",
                    "parkCode": "yose",
                    "organizationName": "National Park Service",
                    "types": ["Event"],
                    "createDate": "2024-01-01",
                    "lastUpdated": "2024-01-10",
                    "infoURL": "https://www.nps.gov/yose",
                    "portalName": "nps.gov",
                },
                {
                    "id": "event2",
                    "title": "Evening Program",
                    "url": "https://www.nps.gov/yose/planyourvisit/event2.htm",
                    "parkFullName": "Yosemite National Park",
                    "description": "Evening educational program.",
                    "latitude": "37.7489",
                    "longitude": "-119.5874",
                    "category": "Education",
                    "subcategory": "Program",
                    "location": "Amphitheater",
                    "tags": ["education", "evening"],
                    "recurrenceDateStart": "",
                    "recurrenceDateEnd": "",
                    "times": [
                        {
                            "timeStart": "19:00",
                            "timeEnd": "20:30",
                            "sunriseTimeStart": "0",  # String boolean
                            "sunsetTimeEnd": "1",  # String boolean
                        }
                    ],
                    "dates": ["2024-01-20"],
                    "dateStart": "2024-01-20",
                    "dateEnd": "2024-01-20",
                    "regresurl": "",
                    "contactEmailAddress": "",
                    "contactTelephoneNumber": "",
                    "feeInfo": "",
                    "isRecurring": "false",  # String boolean
                    "isAllDay": "0",  # String boolean
                    "siteCode": "",
                    "parkCode": "yose",
                    "organizationName": "",
                    "types": [],
                    "createDate": "",
                    "lastUpdated": "",
                    "infoURL": "",
                    "portalName": "",
                },
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetEventsRequest(park_code="yose", limit=10)
            result = get_events(request)

            # Verify response structure
            assert isinstance(result, dict)
            assert "total" in result
            assert "events" in result
            assert "eventsByPark" in result
            assert result["total"] == 2
            assert len(result["events"]) == 2

            # Verify no validation errors occurred
            assert len(result["events"]) == 2

            # Verify event data
            event1 = result["events"][0]
            assert event1["title"] == "Ranger-Led Hike"
            assert event1["parkCode"] == "yose"

            # Verify events grouped by park
            assert "yose" in result["eventsByPark"]
            assert len(result["eventsByPark"]["yose"]) == 2

    def test_get_events_with_parkcode_parameter(self):
        """Test getEvents with parkCode parameter (e.g., 'yose').

        Validates: Requirements 5.4
        """
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "title": "Ranger-Led Hike",
                    "url": "https://www.nps.gov/yose/planyourvisit/event1.htm",
                    "parkFullName": "Yosemite National Park",
                    "description": "Join a ranger for a guided hike.",
                    "parkCode": "yose",
                    "isRecurring": "TRUE",  # Uppercase variant
                    "isAllDay": "FALSE",  # Uppercase variant
                }
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetEventsRequest(park_code="yose", limit=10)
            result = get_events(request)

            # Verify response structure
            assert result["total"] == 1
            assert len(result["events"]) == 1
            assert result["events"][0]["parkCode"] == "yose"

    def test_get_events_with_optional_fields_missing(self):
        """Test getEvents with minimal required fields only.

        Validates: Requirements 5.4
        """
        # Response with only required fields (id and title)
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "title": "Minimal Event",
                    # All other fields are optional and omitted
                }
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetEventsRequest(limit=10)
            # Should not raise validation errors for missing optional fields
            result = get_events(request)

            assert result["total"] == 1
            assert len(result["events"]) == 1
            assert result["events"][0]["title"] == "Minimal Event"

    def test_get_events_no_validation_errors(self):
        """Test that getEvents handles all boolean string variants without errors.

        Validates: Requirements 5.4
        """
        # Test with various boolean string formats
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "test",
                    "title": "Test Event",
                    "url": "https://test.com",
                    "parkCode": "test",
                    "isRecurring": None,  # None value
                    "isAllDay": True,  # Already boolean
                    "times": [
                        {
                            "timeStart": "10:00",
                            "timeEnd": "12:00",
                            "sunriseTimeStart": "",  # Empty string
                            "sunsetTimeEnd": None,  # None value
                        }
                    ],
                }
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetEventsRequest(park_code="test", limit=10)
            # Should not raise any validation errors
            result = get_events(request)

            assert result["total"] == 1
            assert len(result["events"]) == 1

    def test_get_events_with_mixed_boolean_formats(self):
        """Test getEvents with mixed boolean string formats in times.

        Validates: Requirements 5.4
        """
        mock_response = {
            "total": "1",
            "limit": "10",
            "start": "0",
            "data": [
                {
                    "id": "event1",
                    "title": "Sunrise Hike",
                    "parkCode": "yose",
                    "times": [
                        {
                            "timeStart": "06:00",
                            "timeEnd": "08:00",
                            "sunriseTimeStart": "yes",  # Lowercase
                            "sunsetTimeEnd": "NO",  # Uppercase
                        },
                        {
                            "timeStart": None,  # Optional field
                            "timeEnd": None,  # Optional field
                            "sunriseTimeStart": "1",  # String "1"
                            "sunsetTimeEnd": "0",  # String "0"
                        },
                    ],
                }
            ],
        }

        with patch("src.handlers.get_events.get_client") as mock_get_client:
            mock_client = Mock()
            mock_client.get_events.return_value = mock_response
            mock_get_client.return_value = mock_client

            request = GetEventsRequest(park_code="yose", limit=10)
            result = get_events(request)

            assert result["total"] == 1
            assert len(result["events"]) == 1
            assert result["events"][0]["title"] == "Sunrise Hike"
