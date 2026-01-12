"""Unit tests for event model validation.

Tests specific examples and edge cases for EventData and EventTime models.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3
"""

import pytest
from pydantic import ValidationError

from src.models.responses import EventData, EventTime


class TestMinimalEventCreation:
    """Test minimal Event creation with only required fields (id and title)."""

    def test_minimal_event_with_id_and_title_only(self):
        """Test creating EventData with only id and title (Requirements 2.1, 2.5)."""
        event = EventData(id="test-123", title="Test Event")

        assert event.id == "test-123"
        assert event.title == "Test Event"
        # All optional fields should have their defaults
        assert event.url is None
        assert event.description is None
        assert event.date_start is None
        assert event.date_end is None
        assert event.is_recurring is None
        assert event.is_all_day is None
        assert event.park_code is None

    def test_minimal_event_missing_id_fails(self):
        """Test that EventData without id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EventData(title="Test Event")

        assert "id" in str(exc_info.value)

    def test_minimal_event_missing_title_fails(self):
        """Test that EventData without title raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EventData(id="test-123")

        assert "title" in str(exc_info.value)


class TestEventTimeOptionalFields:
    """Test EventTime with all fields omitted (Requirement 2.2)."""

    def test_event_time_with_all_fields_omitted(self):
        """Test creating EventTime with no fields provided."""
        event_time = EventTime()

        assert event_time.time_start is None
        assert event_time.time_end is None
        assert event_time.sunrise_time_start is None
        assert event_time.sunset_time_end is None

    def test_event_time_with_only_time_start(self):
        """Test EventTime with only timeStart provided."""
        event_time = EventTime(timeStart="09:00")

        assert event_time.time_start == "09:00"
        assert event_time.time_end is None
        assert event_time.sunrise_time_start is None
        assert event_time.sunset_time_end is None

    def test_event_time_with_all_fields_provided(self):
        """Test EventTime with all fields provided."""
        event_time = EventTime(
            timeStart="09:00",
            timeEnd="17:00",
            sunriseTimeStart=True,
            sunsetTimeEnd=False,
        )

        assert event_time.time_start == "09:00"
        assert event_time.time_end == "17:00"
        assert event_time.sunrise_time_start is True
        assert event_time.sunset_time_end is False


class TestEventDataOptionalFields:
    """Test EventData with various optional fields present/absent (Requirements 2.3, 2.4)."""

    def test_event_with_url_present(self):
        """Test EventData with url field provided."""
        event = EventData(id="test-123", title="Test Event", url="https://example.com")

        assert event.url == "https://example.com"

    def test_event_with_url_absent(self):
        """Test EventData with url field omitted."""
        event = EventData(id="test-123", title="Test Event")

        assert event.url is None

    def test_event_with_date_fields_present(self):
        """Test EventData with dateStart and dateEnd provided."""
        event = EventData(
            id="test-123",
            title="Test Event",
            dateStart="2024-01-01",
            dateEnd="2024-01-31",
        )

        assert event.date_start == "2024-01-01"
        assert event.date_end == "2024-01-31"

    def test_event_with_date_fields_absent(self):
        """Test EventData with dateStart and dateEnd omitted."""
        event = EventData(id="test-123", title="Test Event")

        assert event.date_start is None
        assert event.date_end is None

    def test_event_with_park_code_present(self):
        """Test EventData with parkCode provided."""
        event = EventData(id="test-123", title="Test Event", parkCode="yose")

        assert event.park_code == "yose"

    def test_event_with_park_code_absent(self):
        """Test EventData with parkCode omitted."""
        event = EventData(id="test-123", title="Test Event")

        assert event.park_code is None

    def test_event_with_mixed_optional_fields(self):
        """Test EventData with some optional fields present and some absent."""
        event = EventData(
            id="test-123",
            title="Test Event",
            url="https://example.com",
            description="A test event",
            # dateStart and dateEnd omitted
            parkCode="yose",
        )

        assert event.url == "https://example.com"
        assert event.description == "A test event"
        assert event.date_start is None
        assert event.date_end is None
        assert event.park_code == "yose"


class TestEventBooleanStringConversion:
    """Test boolean string conversion for event fields (Requirements 3.1, 3.2, 3.3)."""

    def test_is_recurring_yes_converts_to_true(self):
        """Test that 'Yes' string for isRecurring converts to True."""
        event = EventData(id="test-123", title="Test Event", isRecurring="Yes")

        assert event.is_recurring is True

    def test_is_recurring_no_converts_to_false(self):
        """Test that 'No' string for isRecurring converts to False."""
        event = EventData(id="test-123", title="Test Event", isRecurring="No")

        assert event.is_recurring is False

    def test_is_recurring_empty_converts_to_none(self):
        """Test that empty string for isRecurring converts to None."""
        event = EventData(id="test-123", title="Test Event", isRecurring="")

        assert event.is_recurring is None

    def test_is_all_day_yes_converts_to_true(self):
        """Test that 'Yes' string for isAllDay converts to True."""
        event = EventData(id="test-123", title="Test Event", isAllDay="Yes")

        assert event.is_all_day is True

    def test_is_all_day_no_converts_to_false(self):
        """Test that 'No' string for isAllDay converts to False."""
        event = EventData(id="test-123", title="Test Event", isAllDay="No")

        assert event.is_all_day is False

    def test_is_all_day_empty_converts_to_none(self):
        """Test that empty string for isAllDay converts to None."""
        event = EventData(id="test-123", title="Test Event", isAllDay="")

        assert event.is_all_day is None

    def test_boolean_fields_with_true_string(self):
        """Test that 'True' string converts to True for both fields."""
        event = EventData(
            id="test-123", title="Test Event", isRecurring="True", isAllDay="true"
        )

        assert event.is_recurring is True
        assert event.is_all_day is True

    def test_boolean_fields_with_false_string(self):
        """Test that 'False' string converts to False for both fields."""
        event = EventData(
            id="test-123", title="Test Event", isRecurring="False", isAllDay="false"
        )

        assert event.is_recurring is False
        assert event.is_all_day is False

    def test_boolean_fields_with_numeric_strings(self):
        """Test that '1' and '0' strings convert correctly."""
        event = EventData(
            id="test-123", title="Test Event", isRecurring="1", isAllDay="0"
        )

        assert event.is_recurring is True
        assert event.is_all_day is False

    def test_boolean_fields_already_boolean(self):
        """Test that already-boolean values pass through unchanged."""
        event = EventData(
            id="test-123", title="Test Event", isRecurring=True, isAllDay=False
        )

        assert event.is_recurring is True
        assert event.is_all_day is False


class TestEventTimeBooleanStringConversion:
    """Test boolean string conversion for EventTime fields."""

    def test_sunrise_time_start_yes_converts_to_true(self):
        """Test that 'Yes' string for sunriseTimeStart converts to True."""
        event_time = EventTime(sunriseTimeStart="Yes")

        assert event_time.sunrise_time_start is True

    def test_sunrise_time_start_no_converts_to_false(self):
        """Test that 'No' string for sunriseTimeStart converts to False."""
        event_time = EventTime(sunriseTimeStart="No")

        assert event_time.sunrise_time_start is False

    def test_sunrise_time_start_empty_converts_to_none(self):
        """Test that empty string for sunriseTimeStart converts to None."""
        event_time = EventTime(sunriseTimeStart="")

        assert event_time.sunrise_time_start is None

    def test_sunset_time_end_yes_converts_to_true(self):
        """Test that 'Yes' string for sunsetTimeEnd converts to True."""
        event_time = EventTime(sunsetTimeEnd="Yes")

        assert event_time.sunset_time_end is True

    def test_sunset_time_end_no_converts_to_false(self):
        """Test that 'No' string for sunsetTimeEnd converts to False."""
        event_time = EventTime(sunsetTimeEnd="No")

        assert event_time.sunset_time_end is False

    def test_sunset_time_end_empty_converts_to_none(self):
        """Test that empty string for sunsetTimeEnd converts to None."""
        event_time = EventTime(sunsetTimeEnd="")

        assert event_time.sunset_time_end is None

    def test_event_time_boolean_fields_case_insensitive(self):
        """Test that boolean conversion is case-insensitive."""
        event_time = EventTime(sunriseTimeStart="YES", sunsetTimeEnd="no")

        assert event_time.sunrise_time_start is True
        assert event_time.sunset_time_end is False

    def test_event_time_boolean_fields_already_boolean(self):
        """Test that already-boolean values pass through unchanged."""
        event_time = EventTime(sunriseTimeStart=True, sunsetTimeEnd=False)

        assert event_time.sunrise_time_start is True
        assert event_time.sunset_time_end is False


class TestEventDataWithEventTimes:
    """Test EventData with EventTime objects."""

    def test_event_with_empty_times_list(self):
        """Test EventData with empty times list."""
        event = EventData(id="test-123", title="Test Event", times=[])

        assert event.times == []

    def test_event_with_times_list(self):
        """Test EventData with times list containing EventTime objects."""
        event_time1 = EventTime(timeStart="09:00", timeEnd="12:00")
        event_time2 = EventTime(timeStart="14:00", timeEnd="17:00")

        event = EventData(
            id="test-123", title="Test Event", times=[event_time1, event_time2]
        )

        assert len(event.times) == 2
        assert event.times[0].time_start == "09:00"
        assert event.times[1].time_start == "14:00"

    def test_event_with_times_as_dicts(self):
        """Test EventData with times provided as dictionaries."""
        event = EventData(
            id="test-123",
            title="Test Event",
            times=[
                {"timeStart": "09:00", "timeEnd": "12:00"},
                {"timeStart": "14:00", "timeEnd": "17:00"},
            ],
        )

        assert len(event.times) == 2
        assert event.times[0].time_start == "09:00"
        assert event.times[1].time_start == "14:00"
