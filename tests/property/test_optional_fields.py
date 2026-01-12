"""Property-based tests for optional field handling in models.

Feature: mcp-validation-fixes
Tests Properties 6-7 for optional field handling logic.
"""

from typing import Any, Dict, Optional

from hypothesis import given
from hypothesis import strategies as st

from src.models.responses import EventData, EventTime

# Strategy for generating optional string values
optional_string = st.one_of(st.none(), st.text(min_size=1, max_size=50))

# Strategy for generating optional boolean values
optional_bool = st.one_of(st.none(), st.booleans())

# Strategy for generating lists of strings
string_list = st.lists(st.text(min_size=1, max_size=20), max_size=5)


# Feature: mcp-validation-fixes, Property 6: Optional Fields Default to None When Omitted
@given(
    st.sampled_from(
        [
            "url",
            "description",
            "latitude",
            "longitude",
            "category",
            "location",
            "date_start",
            "date_end",
            "is_recurring",
            "is_all_day",
            "park_code",
        ]
    )
)
def test_optional_fields_default_to_none_when_omitted(field_name: str):
    """For any optional field in EventData, when omitted, should default to None.

    Validates: Requirements 2.3
    """
    # Create minimal EventData with only required fields
    data = {"id": "test-id-123", "title": "Test Event Title"}

    event = EventData(**data)

    # Convert camelCase to snake_case for Python attribute access
    python_field_name = field_name
    if field_name == "date_start":
        python_field_name = "date_start"
    elif field_name == "date_end":
        python_field_name = "date_end"
    elif field_name == "is_recurring":
        python_field_name = "is_recurring"
    elif field_name == "is_all_day":
        python_field_name = "is_all_day"
    elif field_name == "park_code":
        python_field_name = "park_code"

    field_value = getattr(event, python_field_name)

    assert (
        field_value is None
    ), f"Expected None for omitted field '{field_name}', got {field_value}"


# Feature: mcp-validation-fixes, Property 6: Optional Fields Default to None When Omitted (EventTime)
@given(
    st.sampled_from(["time_start", "time_end", "sunrise_time_start", "sunset_time_end"])
)
def test_event_time_optional_fields_default_to_none_when_omitted(field_name: str):
    """For any optional field in EventTime, when omitted, should default to None.

    Validates: Requirements 2.2, 2.3
    """
    # Create EventTime with no fields
    event_time = EventTime()

    field_value = getattr(event_time, field_name)

    assert (
        field_value is None
    ), f"Expected None for omitted field '{field_name}', got {field_value}"


# Feature: mcp-validation-fixes, Property 7: Optional Fields Store Values When Provided
@given(
    optional_string,
    optional_string,
    optional_string,
    optional_string,
    optional_string,
    optional_string,
    optional_string,
    optional_string,
    optional_bool,
    optional_bool,
    optional_string,
)
def test_optional_fields_store_values_when_provided(
    url: Optional[str],
    description: Optional[str],
    latitude: Optional[str],
    longitude: Optional[str],
    category: Optional[str],
    location: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    is_recurring: Optional[bool],
    is_all_day: Optional[bool],
    park_code: Optional[str],
):
    """For any optional field in EventData, when provided, should store the value.

    Validates: Requirements 2.4
    """
    # Build data dict with only non-None values
    data: Dict[str, Any] = {
        "id": "test-id-456",
        "title": "Test Event With Optional Fields",
    }

    if url is not None:
        data["url"] = url
    if description is not None:
        data["description"] = description
    if latitude is not None:
        data["latitude"] = latitude
    if longitude is not None:
        data["longitude"] = longitude
    if category is not None:
        data["category"] = category
    if location is not None:
        data["location"] = location
    if date_start is not None:
        data["dateStart"] = date_start
    if date_end is not None:
        data["dateEnd"] = date_end
    if is_recurring is not None:
        data["isRecurring"] = is_recurring
    if is_all_day is not None:
        data["isAllDay"] = is_all_day
    if park_code is not None:
        data["parkCode"] = park_code

    event = EventData(**data)

    # Verify each provided field is stored correctly
    if url is not None:
        assert event.url == url, f"Expected url={url}, got {event.url}"
    if description is not None:
        assert (
            event.description == description
        ), f"Expected description={description}, got {event.description}"
    if latitude is not None:
        assert (
            event.latitude == latitude
        ), f"Expected latitude={latitude}, got {event.latitude}"
    if longitude is not None:
        assert (
            event.longitude == longitude
        ), f"Expected longitude={longitude}, got {event.longitude}"
    if category is not None:
        assert (
            event.category == category
        ), f"Expected category={category}, got {event.category}"
    if location is not None:
        assert (
            event.location == location
        ), f"Expected location={location}, got {event.location}"
    if date_start is not None:
        assert (
            event.date_start == date_start
        ), f"Expected date_start={date_start}, got {event.date_start}"
    if date_end is not None:
        assert (
            event.date_end == date_end
        ), f"Expected date_end={date_end}, got {event.date_end}"
    if is_recurring is not None:
        assert (
            event.is_recurring == is_recurring
        ), f"Expected is_recurring={is_recurring}, got {event.is_recurring}"
    if is_all_day is not None:
        assert (
            event.is_all_day == is_all_day
        ), f"Expected is_all_day={is_all_day}, got {event.is_all_day}"
    if park_code is not None:
        assert (
            event.park_code == park_code
        ), f"Expected park_code={park_code}, got {event.park_code}"


# Feature: mcp-validation-fixes, Property 7: Optional Fields Store Values When Provided (EventTime)
@given(optional_string, optional_string, optional_bool, optional_bool)
def test_event_time_optional_fields_store_values_when_provided(
    time_start: Optional[str],
    time_end: Optional[str],
    sunrise_time_start: Optional[bool],
    sunset_time_end: Optional[bool],
):
    """For any optional field in EventTime, when provided, should store the value.

    Validates: Requirements 2.2, 2.4
    """
    # Build data dict with only non-None values
    data: Dict[str, Any] = {}

    if time_start is not None:
        data["timeStart"] = time_start
    if time_end is not None:
        data["timeEnd"] = time_end
    if sunrise_time_start is not None:
        data["sunriseTimeStart"] = sunrise_time_start
    if sunset_time_end is not None:
        data["sunsetTimeEnd"] = sunset_time_end

    event_time = EventTime(**data)

    # Verify each provided field is stored correctly
    if time_start is not None:
        assert (
            event_time.time_start == time_start
        ), f"Expected time_start={time_start}, got {event_time.time_start}"
    if time_end is not None:
        assert (
            event_time.time_end == time_end
        ), f"Expected time_end={time_end}, got {event_time.time_end}"
    if sunrise_time_start is not None:
        assert event_time.sunrise_time_start == sunrise_time_start, (
            f"Expected sunrise_time_start={sunrise_time_start}, "
            f"got {event_time.sunrise_time_start}"
        )
    if sunset_time_end is not None:
        assert event_time.sunset_time_end == sunset_time_end, (
            f"Expected sunset_time_end={sunset_time_end}, "
            f"got {event_time.sunset_time_end}"
        )
