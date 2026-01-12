# Fix MCP National Parks Validation Issues

## Problem Description

The National Parks MCP server has critical validation errors in two endpoints that are preventing proper functionality:

### 1. getCampgrounds Endpoint - Boolean Parsing Errors
**Error Type:** `bool_parsing` validation failures
**Affected Fields:**
- `amenities.trashRecyclingCollection`
- `amenities.staffOrVolunteerHostOnsite`
- `amenities.foodStorageLockers`
- `amenities.cellPhoneReception`

**Root Cause:** The NPS API returns string values like "Yes", "No", "Unknown", or empty strings for boolean fields, but our Pydantic models expect strict boolean types.

### 2. getEvents Endpoint - Missing Required Fields
**Error Type:** `missing` field validation failures
**Affected Fields:**
- `url` (required but missing from API response)
- `times[].timeStart` (required but missing)
- `times[].timeEnd` (required but missing)
- `times[].sunriseTimeStart` (required but missing)
- `times[].sunsetTimeEnd` (required but missing)
- `dateStart` (required but missing)
- `dateEnd` (required but missing)
- `isRecurring` (required but missing)
- `isAllDay` (required but missing)
- `parkCode` (required but missing)

**Root Cause:** Our Pydantic models define fields as required that are actually optional in the NPS API responses.

## Detailed Fix Instructions

### Step 1: Fix getCampgrounds Boolean Parsing

**File to modify:** `src/models/campground.py` (or wherever campground models are defined)

**Problem:** Boolean fields are receiving string values from NPS API
**Solution:** Create a custom validator that converts string values to booleans

```python
from pydantic import BaseModel, field_validator
from typing import Optional, Union

class CampgroundAmenities(BaseModel):
    trashRecyclingCollection: Optional[bool] = None
    staffOrVolunteerHostOnsite: Optional[bool] = None
    foodStorageLockers: Optional[bool] = None
    cellPhoneReception: Optional[bool] = None

    @field_validator('trashRecyclingCollection', 'staffOrVolunteerHostOnsite', 'foodStorageLockers', 'cellPhoneReception', mode='before')
    @classmethod
    def parse_boolean_strings(cls, v: Union[str, bool, None]) -> Optional[bool]:
        """Convert string boolean values from NPS API to actual booleans"""
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ['yes', 'true', '1']:
                return True
            elif v_lower in ['no', 'false', '0']:
                return False
            elif v_lower in ['unknown', 'n/a', 'not available']:
                return None
        return None
```

### Step 2: Fix getEvents Missing Required Fields

**File to modify:** `src/models/event.py` (or wherever event models are defined)

**Problem:** Fields marked as required are actually optional in NPS API
**Solution:** Make fields optional and provide sensible defaults

```python
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime

class EventTime(BaseModel):
    timeStart: Optional[str] = None
    timeEnd: Optional[str] = None
    sunriseTimeStart: Optional[str] = None
    sunsetTimeEnd: Optional[str] = None

class Event(BaseModel):
    # Core fields that should be present
    id: str
    title: str
    description: Optional[str] = None

    # Previously required fields that should be optional
    url: Optional[str] = None
    dateStart: Optional[str] = None
    dateEnd: Optional[str] = None
    isRecurring: Optional[bool] = None
    isAllDay: Optional[bool] = None
    parkCode: Optional[str] = None

    # Times array with optional fields
    times: List[EventTime] = []

    @field_validator('isRecurring', 'isAllDay', mode='before')
    @classmethod
    def parse_boolean_fields(cls, v: Union[str, bool, None]) -> Optional[bool]:
        """Convert string boolean values to actual booleans"""
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ['yes', 'true', '1']:
                return True
            elif v_lower in ['no', 'false', '0']:
                return False
        return None
```

### Step 3: Update Handler Functions

**Files to check and update:**
- `src/handlers/get_campgrounds.py`
- `src/handlers/get_events.py`

**Ensure proper error handling:**

```python
# In get_campgrounds.py
async def get_campgrounds(parkCode: Optional[str] = None, limit: Optional[int] = 10, start: Optional[int] = 0, q: Optional[str] = None):
    try:
        # Your existing API call logic
        response = await make_nps_api_call(...)

        # Validate and parse response
        campgrounds = []
        for item in response.get('data', []):
            try:
                campground = Campground.model_validate(item)
                campgrounds.append(campground)
            except ValidationError as e:
                # Log the validation error but continue processing other items
                print(f"Validation error for campground {item.get('name', 'unknown')}: {e}")
                continue

        return {
            "total": response.get('total', len(campgrounds)),
            "limit": limit,
            "start": start,
            "campgrounds": campgrounds
        }
    except Exception as e:
        return {"error": "processing_error", "message": str(e)}

# Similar pattern for get_events.py
```

### Step 4: Add Comprehensive Tests

**Create/Update test files:**

```python
# tests/unit/test_campgrounds.py
import pytest
from src.models.campground import CampgroundAmenities, Campground

def test_campground_amenities_boolean_parsing():
    """Test that string boolean values are properly converted"""

    # Test "Yes" strings
    amenities_data = {
        "trashRecyclingCollection": "Yes",
        "staffOrVolunteerHostOnsite": "YES",
        "foodStorageLockers": "yes",
        "cellPhoneReception": "True"
    }
    amenities = CampgroundAmenities.model_validate(amenities_data)
    assert amenities.trashRecyclingCollection is True
    assert amenities.staffOrVolunteerHostOnsite is True
    assert amenities.foodStorageLockers is True
    assert amenities.cellPhoneReception is True

    # Test "No" strings
    amenities_data = {
        "trashRecyclingCollection": "No",
        "staffOrVolunteerHostOnsite": "NO",
        "foodStorageLockers": "no",
        "cellPhoneReception": "False"
    }
    amenities = CampgroundAmenities.model_validate(amenities_data)
    assert amenities.trashRecyclingCollection is False
    assert amenities.staffOrVolunteerHostOnsite is False
    assert amenities.foodStorageLockers is False
    assert amenities.cellPhoneReception is False

    # Test unknown/empty values
    amenities_data = {
        "trashRecyclingCollection": "Unknown",
        "staffOrVolunteerHostOnsite": "",
        "foodStorageLockers": "N/A",
        "cellPhoneReception": None
    }
    amenities = CampgroundAmenities.model_validate(amenities_data)
    assert amenities.trashRecyclingCollection is None
    assert amenities.staffOrVolunteerHostOnsite is None
    assert amenities.foodStorageLockers is None
    assert amenities.cellPhoneReception is None

# tests/unit/test_events.py
import pytest
from src.models.event import Event, EventTime

def test_event_optional_fields():
    """Test that events can be created with minimal required fields"""

    # Minimal event data
    event_data = {
        "id": "test-event-1",
        "title": "Test Event"
    }
    event = Event.model_validate(event_data)
    assert event.id == "test-event-1"
    assert event.title == "Test Event"
    assert event.url is None
    assert event.dateStart is None
    assert event.isRecurring is None
    assert event.times == []

def test_event_boolean_parsing():
    """Test boolean field parsing for events"""

    event_data = {
        "id": "test-event-1",
        "title": "Test Event",
        "isRecurring": "Yes",
        "isAllDay": "No"
    }
    event = Event.model_validate(event_data)
    assert event.isRecurring is True
    assert event.isAllDay is False

# tests/integration/test_mcp_endpoints.py
import pytest
from src.handlers.get_campgrounds import get_campgrounds
from src.handlers.get_events import get_events

@pytest.mark.asyncio
async def test_get_campgrounds_integration():
    """Test that getCampgrounds endpoint works without validation errors"""
    result = await get_campgrounds(parkCode="yose", limit=2)

    # Should not have validation errors
    assert "error" not in result or result.get("error") != "validation_error"
    assert "campgrounds" in result
    assert isinstance(result["campgrounds"], list)

@pytest.mark.asyncio
async def test_get_events_integration():
    """Test that getEvents endpoint works without validation errors"""
    result = await get_events(parkCode="yose", limit=2)

    # Should not have validation errors
    assert "error" not in result or result.get("error") != "validation_error"
    # Events might be empty, but structure should be correct
    assert "total" in result or "events" in result
```

## Execution Instructions

### Phase 1: Implement Fixes
1. **Update Pydantic Models**: Modify campground and event models with proper field validators
2. **Update Handler Functions**: Ensure proper error handling and validation
3. **Test Data Validation**: Create unit tests for the new validation logic

### Phase 2: Test and Iterate
1. **Run Unit Tests**: Execute all unit tests to verify model validation works
   ```bash
   python -m pytest tests/unit/ -v
   ```

2. **Run Integration Tests**: Test the actual MCP endpoints
   ```bash
   python -m pytest tests/integration/ -v
   ```

3. **Manual MCP Testing**: Test the actual MCP server endpoints
   ```bash
   # Test getCampgrounds
   python -c "
   import asyncio
   from src.handlers.get_campgrounds import get_campgrounds
   result = asyncio.run(get_campgrounds(parkCode='yose', limit=2))
   print('getCampgrounds result:', result)
   "

   # Test getEvents
   python -c "
   import asyncio
   from src.handlers.get_events import get_events
   result = asyncio.run(get_events(parkCode='yose', limit=2))
   print('getEvents result:', result)
   "
   ```

### Phase 3: Fix-Test Loop
**CRITICAL**: Continue this loop until ALL tests pass:

1. **Run all tests**
2. **If any test fails**:
   - Analyze the failure
   - Fix the specific issue
   - Run tests again
3. **Repeat until zero test failures**
4. **Verify MCP endpoints work correctly**

### Success Criteria
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ getCampgrounds returns data without validation errors
- ✅ getEvents returns data without validation errors
- ✅ Manual MCP testing shows both endpoints working

## Common Pitfalls to Avoid

1. **Don't make all fields required** - NPS API has inconsistent data
2. **Handle edge cases in validators** - Empty strings, "Unknown", "N/A" values
3. **Graceful degradation** - If one item fails validation, continue processing others
4. **Proper error logging** - Log validation failures for debugging
5. **Test with real API data** - Don't just test with mock data

## Final Verification

After implementing all fixes, verify success by running:

```bash
# Full test suite
python -m pytest tests/ -v

# Manual endpoint verification
python test_mcp_endpoints_manual.py
```

Both getCampgrounds and getEvents should return valid data structures without any validation errors.
