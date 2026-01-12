"""Unit tests for campground model validation.

Tests specific examples and edge cases for CampgroundAmenities boolean conversion.
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from src.models.responses import CampgroundAmenities


def create_minimal_amenities(**overrides):
    """Create minimal CampgroundAmenities with defaults."""
    data = {
        "trashRecyclingCollection": False,
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
    }
    data.update(overrides)
    return CampgroundAmenities(**data)


class TestBooleanStringConversion:
    """Test boolean string conversion for specific examples."""

    def test_yes_converts_to_true(self):
        """Test that 'Yes' string converts to True."""
        amenities = create_minimal_amenities(trashRecyclingCollection="Yes")
        assert amenities.trash_recycling_collection is True

    def test_no_converts_to_false(self):
        """Test that 'No' string converts to False."""
        amenities = create_minimal_amenities(staffOrVolunteerHostOnsite="No")
        assert amenities.staff_or_volunteer_host_onsite is False

    def test_unknown_converts_to_none(self):
        """Test that 'Unknown' string converts to None."""
        amenities = create_minimal_amenities(foodStorageLockers="Unknown")
        assert amenities.food_storage_lockers is None


class TestEdgeCases:
    """Test edge cases for boolean conversion."""

    def test_empty_string_converts_to_none(self):
        """Test that empty string converts to None."""
        amenities = create_minimal_amenities(cellPhoneReception="")
        assert amenities.cell_phone_reception is None

    def test_none_value_stays_none(self):
        """Test that None value stays None."""
        amenities = create_minimal_amenities(trashRecyclingCollection=None)
        assert amenities.trash_recycling_collection is None

    def test_already_boolean_true_passes_through(self):
        """Test that already-boolean True value passes through."""
        amenities = create_minimal_amenities(laundry=True)
        assert amenities.laundry is True

    def test_already_boolean_false_passes_through(self):
        """Test that already-boolean False value passes through."""
        amenities = create_minimal_amenities(amphitheater=False)
        assert amenities.amphitheater is False


class TestAllFourAmenityFields:
    """Test all four amenity fields individually."""

    def test_trash_recycling_collection_field(self):
        """Test trashRecyclingCollection field conversion."""
        # Test Yes -> True
        amenities = create_minimal_amenities(trashRecyclingCollection="Yes")
        assert amenities.trash_recycling_collection is True

        # Test No -> False
        amenities = create_minimal_amenities(trashRecyclingCollection="No")
        assert amenities.trash_recycling_collection is False

        # Test Unknown -> None
        amenities = create_minimal_amenities(trashRecyclingCollection="Unknown")
        assert amenities.trash_recycling_collection is None

    def test_staff_or_volunteer_host_onsite_field(self):
        """Test staffOrVolunteerHostOnsite field conversion."""
        # Test Yes -> True
        amenities = create_minimal_amenities(staffOrVolunteerHostOnsite="Yes")
        assert amenities.staff_or_volunteer_host_onsite is True

        # Test No -> False
        amenities = create_minimal_amenities(staffOrVolunteerHostOnsite="No")
        assert amenities.staff_or_volunteer_host_onsite is False

        # Test Unknown -> None
        amenities = create_minimal_amenities(staffOrVolunteerHostOnsite="Unknown")
        assert amenities.staff_or_volunteer_host_onsite is None

    def test_food_storage_lockers_field(self):
        """Test foodStorageLockers field conversion."""
        # Test Yes -> True
        amenities = create_minimal_amenities(foodStorageLockers="Yes")
        assert amenities.food_storage_lockers is True

        # Test No -> False
        amenities = create_minimal_amenities(foodStorageLockers="No")
        assert amenities.food_storage_lockers is False

        # Test Unknown -> None
        amenities = create_minimal_amenities(foodStorageLockers="Unknown")
        assert amenities.food_storage_lockers is None

    def test_cell_phone_reception_field(self):
        """Test cellPhoneReception field conversion."""
        # Test Yes -> True
        amenities = create_minimal_amenities(cellPhoneReception="Yes")
        assert amenities.cell_phone_reception is True

        # Test No -> False
        amenities = create_minimal_amenities(cellPhoneReception="No")
        assert amenities.cell_phone_reception is False

        # Test Unknown -> None
        amenities = create_minimal_amenities(cellPhoneReception="Unknown")
        assert amenities.cell_phone_reception is None


class TestCaseInsensitivity:
    """Test that conversion is case-insensitive."""

    def test_uppercase_yes(self):
        """Test uppercase YES converts to True."""
        amenities = create_minimal_amenities(trashRecyclingCollection="YES")
        assert amenities.trash_recycling_collection is True

    def test_lowercase_no(self):
        """Test lowercase no converts to False."""
        amenities = create_minimal_amenities(staffOrVolunteerHostOnsite="no")
        assert amenities.staff_or_volunteer_host_onsite is False

    def test_mixed_case_true(self):
        """Test mixed case True converts to True."""
        amenities = create_minimal_amenities(foodStorageLockers="TrUe")
        assert amenities.food_storage_lockers is True

    def test_mixed_case_false(self):
        """Test mixed case False converts to False."""
        amenities = create_minimal_amenities(cellPhoneReception="FaLsE")
        assert amenities.cell_phone_reception is False
