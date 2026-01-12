"""Property-based tests for boolean string conversion in models.

Feature: mcp-validation-fixes
Tests Properties 1-5 for boolean conversion logic.
"""

from typing import Optional, Union

from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, field_validator

from src.models.responses import CampgroundAmenities


# Test helper model to test the conversion logic in isolation
class BooleanTestModel(BaseModel):
    """Test model with boolean field validator."""

    test_field: Optional[bool] = None

    @field_validator("test_field", mode="before")
    @classmethod
    def parse_boolean_strings(cls, v: Union[str, bool, None]) -> Optional[bool]:
        """Convert string boolean values to actual booleans."""
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ["yes", "true", "1"]:
                return True
            elif v_lower in ["no", "false", "0"]:
                return False
            elif v_lower in ["unknown", "n/a", "not available"]:
                return None
        return None


# Feature: mcp-validation-fixes, Property 1: Affirmative String to Boolean Conversion
@given(st.sampled_from(["Yes", "YES", "yes", "True", "TRUE", "true", "1"]))
def test_affirmative_string_to_boolean_conversion(value: str):
    """For any affirmative string value, the field validator should convert to True.

    Validates: Requirements 1.1, 3.1
    """
    model = BooleanTestModel(test_field=value)
    assert (
        model.test_field is True
    ), f"Expected True for '{value}', got {model.test_field}"


# Feature: mcp-validation-fixes, Property 2: Negative String to Boolean Conversion
@given(st.sampled_from(["No", "NO", "no", "False", "FALSE", "false", "0"]))
def test_negative_string_to_boolean_conversion(value: str):
    """For any negative string value, the field validator should convert to False.

    Validates: Requirements 1.2, 3.2
    """
    model = BooleanTestModel(test_field=value)
    assert (
        model.test_field is False
    ), f"Expected False for '{value}', got {model.test_field}"


# Feature: mcp-validation-fixes, Property 3: Unknown String to None Conversion
@given(
    st.sampled_from(
        [
            "Unknown",
            "UNKNOWN",
            "unknown",
            "N/A",
            "n/a",
            "Not Available",
            "not available",
            "",
            None,
        ]
    )
)
def test_unknown_string_to_none_conversion(value: Optional[str]):
    """For any unknown value, the field validator should convert to None.

    Validates: Requirements 1.3, 3.3
    """
    model = BooleanTestModel(test_field=value)
    assert (
        model.test_field is None
    ), f"Expected None for '{value}', got {model.test_field}"


# Feature: mcp-validation-fixes, Property 4: Boolean Pass-Through (Idempotence)
@given(st.booleans())
def test_boolean_passthrough_idempotence(value: bool):
    """For any already-boolean value, the field validator should return it unchanged.

    Validates: Requirements 1.5
    """
    model = BooleanTestModel(test_field=value)
    assert (
        model.test_field == value
    ), f"Expected {value} to pass through unchanged, got {model.test_field}"


# Feature: mcp-validation-fixes, Property 5: Campground Amenity Fields Apply Conversion
@given(
    st.sampled_from(["Yes", "No", "Unknown", "yes", "no", "true", "false", "1", "0"]),
    st.sampled_from(
        [
            "trashRecyclingCollection",
            "staffOrVolunteerHostOnsite",
            "foodStorageLockers",
            "cellPhoneReception",
        ]
    ),
)
def test_campground_amenity_fields_apply_conversion(value: str, field_name: str):
    """For any of the four campground amenity boolean fields, string values should be converted.

    Validates: Requirements 1.4
    """
    # Create a minimal campground amenities object with the field set
    data = {
        field_name: value,
        "toilets": [],
        "internetConnectivity": False,
        "showers": [],
        "laundry": False,
        "amphitheater": False,
        "dumpStation": False,
        "campStore": False,
        "potableWater": [],
        "iceAvailableForSale": False,
        "firewoodForSale": False,
    }

    # This should not raise a validation error
    amenities = CampgroundAmenities(**data)

    # Get the field value using the Python field name (snake_case)
    python_field_name = field_name.replace(
        "trashRecyclingCollection", "trash_recycling_collection"
    )
    python_field_name = python_field_name.replace(
        "staffOrVolunteerHostOnsite", "staff_or_volunteer_host_onsite"
    )
    python_field_name = python_field_name.replace(
        "foodStorageLockers", "food_storage_lockers"
    )
    python_field_name = python_field_name.replace(
        "cellPhoneReception", "cell_phone_reception"
    )

    field_value = getattr(amenities, python_field_name)

    # Verify the conversion happened correctly
    if value.lower() in ["yes", "true", "1"]:
        assert (
            field_value is True
        ), f"Expected True for '{value}' in {field_name}, got {field_value}"
    elif value.lower() in ["no", "false", "0"]:
        assert (
            field_value is False
        ), f"Expected False for '{value}' in {field_name}, got {field_value}"
    elif value.lower() in ["unknown"]:
        assert (
            field_value is None
        ), f"Expected None for '{value}' in {field_name}, got {field_value}"


# Event-specific boolean conversion tests


# Feature: mcp-validation-fixes, Property 1: Affirmative String to Boolean Conversion (for event fields)
@given(
    st.sampled_from(["Yes", "YES", "yes", "True", "TRUE", "true", "1"]),
    st.sampled_from(["isRecurring", "isAllDay", "sunriseTimeStart", "sunsetTimeEnd"]),
)
def test_event_affirmative_string_to_boolean_conversion(value: str, field_name: str):
    """For any event boolean field with affirmative string, should convert to True.

    Validates: Requirements 3.1
    """
    from src.models.responses import EventData, EventTime

    if field_name in ["isRecurring", "isAllDay"]:
        # Test EventData fields
        data = {"id": "test-id", "title": "Test Event", field_name: value}
        event = EventData(**data)

        # Get the field value using the Python field name (snake_case)
        python_field_name = (
            "is_recurring" if field_name == "isRecurring" else "is_all_day"
        )
        field_value = getattr(event, python_field_name)

        assert (
            field_value is True
        ), f"Expected True for '{value}' in {field_name}, got {field_value}"
    else:
        # Test EventTime fields
        data = {field_name: value}
        event_time = EventTime(**data)

        # Get the field value using the Python field name (snake_case)
        python_field_name = (
            "sunrise_time_start"
            if field_name == "sunriseTimeStart"
            else "sunset_time_end"
        )
        field_value = getattr(event_time, python_field_name)

        assert (
            field_value is True
        ), f"Expected True for '{value}' in {field_name}, got {field_value}"


# Feature: mcp-validation-fixes, Property 2: Negative String to Boolean Conversion (for event fields)
@given(
    st.sampled_from(["No", "NO", "no", "False", "FALSE", "false", "0"]),
    st.sampled_from(["isRecurring", "isAllDay", "sunriseTimeStart", "sunsetTimeEnd"]),
)
def test_event_negative_string_to_boolean_conversion(value: str, field_name: str):
    """For any event boolean field with negative string, should convert to False.

    Validates: Requirements 3.2
    """
    from src.models.responses import EventData, EventTime

    if field_name in ["isRecurring", "isAllDay"]:
        # Test EventData fields
        data = {"id": "test-id", "title": "Test Event", field_name: value}
        event = EventData(**data)

        # Get the field value using the Python field name (snake_case)
        python_field_name = (
            "is_recurring" if field_name == "isRecurring" else "is_all_day"
        )
        field_value = getattr(event, python_field_name)

        assert (
            field_value is False
        ), f"Expected False for '{value}' in {field_name}, got {field_value}"
    else:
        # Test EventTime fields
        data = {field_name: value}
        event_time = EventTime(**data)

        # Get the field value using the Python field name (snake_case)
        python_field_name = (
            "sunrise_time_start"
            if field_name == "sunriseTimeStart"
            else "sunset_time_end"
        )
        field_value = getattr(event_time, python_field_name)

        assert (
            field_value is False
        ), f"Expected False for '{value}' in {field_name}, got {field_value}"


# Feature: mcp-validation-fixes, Property 3: Unknown String to None Conversion (for event fields)
@given(
    st.sampled_from(["", None]),
    st.sampled_from(["isRecurring", "isAllDay", "sunriseTimeStart", "sunsetTimeEnd"]),
)
def test_event_unknown_string_to_none_conversion(value: Optional[str], field_name: str):
    """For any event boolean field with empty/None value, should convert to None.

    Validates: Requirements 3.3
    """
    from src.models.responses import EventData, EventTime

    if field_name in ["isRecurring", "isAllDay"]:
        # Test EventData fields
        data = {"id": "test-id", "title": "Test Event", field_name: value}
        event = EventData(**data)

        # Get the field value using the Python field name (snake_case)
        python_field_name = (
            "is_recurring" if field_name == "isRecurring" else "is_all_day"
        )
        field_value = getattr(event, python_field_name)

        assert (
            field_value is None
        ), f"Expected None for '{value}' in {field_name}, got {field_value}"
    else:
        # Test EventTime fields
        data = {field_name: value}
        event_time = EventTime(**data)

        # Get the field value using the Python field name (snake_case)
        python_field_name = (
            "sunrise_time_start"
            if field_name == "sunriseTimeStart"
            else "sunset_time_end"
        )
        field_value = getattr(event_time, python_field_name)

        assert (
            field_value is None
        ), f"Expected None for '{value}' in {field_name}, got {field_value}"
