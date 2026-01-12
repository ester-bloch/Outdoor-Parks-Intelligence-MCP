# Fix MCP National Parks Validation Issues

## Problem Description

The MCP National Parks server has validation errors in two endpoints that need to be fixed:

### 1. getCampgrounds Endpoint - Boolean Parsing Issues

**Error Details:**
```
validation_error: Input validation failed
- amenities.trashRecyclingCollection: Input should be a valid boolean, unable to interpret input
- amenities.staffOrVolunteerHostOnsite: Input should be a valid boolean, unable to interpret input
- amenities.foodStorageLockers: Input should be a valid boolean, unable to interpret input
- amenities.cellPhoneReception: Input should be a valid boolean, unable to interpret input
```

**Root Cause:** The National Park Service API returns boolean values as strings ("Yes"/"No" or "True"/"False") but the Pydantic models expect actual boolean types.

### 2. getEvents Endpoint - Missing Required Fields

**Error Details:**
```
validation_error: Input validation failed
- Multiple missing required fields in event data structure including:
  - url (required)
  - times[].timeStart (required)
  - times[].timeEnd (required)
  - times[].sunriseTimeStart (required)
  - times[].sunsetTimeEnd (required)
  - dateStart (required)
  - dateEnd (required)
  - isRecurring (required)
  - isAllDay (required)
  - parkCode (required)
```

**Root Cause:** The Pydantic models have fields marked as required that are actually optional in the NPS API response, or the field mapping is incorrect.

## Solution Strategy

### For getCampgrounds (Boolean Parsing):

1. **Identify the Data Transformation Issue:**
   - The NPS API returns strings like "Yes"/"No" for boolean fields
   - Pydantic models expect actual boolean values
   - Need to add data transformation before validation

2. **Implementation Approach:**
   - Add a preprocessing function to convert string booleans to actual booleans
   - Handle various string formats: "Yes"/"No", "True"/"False", "1"/"0"
   - Apply this transformation before Pydantic validation

3. **Code Changes Needed:**
   ```python
   def normalize_boolean_fields(data: dict) -> dict:
       """Convert string boolean values to actual booleans"""
       boolean_mappings = {
           "Yes": True, "No": False,
           "True": True, "False": False,
           "1": True, "0": False,
           "true": True, "false": False,
           "yes": True, "no": False
       }

       # Apply to amenities fields
       if "amenities" in data:
           for key, value in data["amenities"].items():
               if isinstance(value, str) and value in boolean_mappings:
                   data["amenities"][key] = boolean_mappings[value]

       return data
   ```

### For getEvents (Missing Required Fields):

1. **Review Pydantic Model Definitions:**
   - Check which fields are marked as required vs optional
   - Compare with actual NPS API response structure
   - Make fields optional where NPS API doesn't guarantee them

2. **Implementation Approach:**
   - Change required fields to Optional[Type] where appropriate
   - Add default values for missing fields
   - Use Field(default=None) for optional fields

3. **Code Changes Needed:**
   ```python
   from typing import Optional
   from pydantic import Field

   class EventTime(BaseModel):
       timeStart: Optional[str] = Field(default=None)
       timeEnd: Optional[str] = Field(default=None)
       sunriseTimeStart: Optional[str] = Field(default=None)
       sunsetTimeEnd: Optional[str] = Field(default=None)

   class Event(BaseModel):
       url: Optional[str] = Field(default="")
       dateStart: Optional[str] = Field(default=None)
       dateEnd: Optional[str] = Field(default=None)
       isRecurring: Optional[bool] = Field(default=False)
       isAllDay: Optional[bool] = Field(default=False)
       parkCode: Optional[str] = Field(default=None)
   ```

## Detailed Fix Instructions

### Step 1: Locate the Relevant Files

Find and examine these files in your codebase:
- `src/handlers/get_campgrounds.py` (or similar)
- `src/handlers/get_events.py` (or similar)
- `src/models/` directory for Pydantic model definitions
- Any shared utility functions for data processing

### Step 2: Fix getCampgrounds Boolean Issue

1. **Add Boolean Normalization Function:**
   ```python
   def normalize_campground_data(campground_data: dict) -> dict:
       """Normalize campground data from NPS API format to expected format"""

       def str_to_bool(value):
           if isinstance(value, str):
               return value.lower() in ['yes', 'true', '1']
           return bool(value) if value is not None else False

       # Handle amenities boolean fields
       if "amenities" in campground_data:
           amenities = campground_data["amenities"]
           boolean_fields = [
               "trashRecyclingCollection",
               "staffOrVolunteerHostOnsite",
               "foodStorageLockers",
               "cellPhoneReception"
           ]

           for field in boolean_fields:
               if field in amenities:
                   amenities[field] = str_to_bool(amenities[field])

       return campground_data
   ```

2. **Apply Normalization in Handler:**
   ```python
   async def get_campgrounds(parkCode: str = None, limit: int = 10, start: int = 0, q: str = None):
       # ... existing API call code ...

       # Normalize data before validation
       normalized_campgrounds = []
       for campground in raw_campgrounds:
           normalized_campground = normalize_campground_data(campground)
           normalized_campgrounds.append(normalized_campground)

       # Now validate with Pydantic models
       validated_campgrounds = [CampgroundModel(**camp) for camp in normalized_campgrounds]
   ```

### Step 3: Fix getEvents Missing Fields Issue

1. **Update Event Pydantic Models:**
   ```python
   from typing import Optional, List
   from pydantic import BaseModel, Field

   class EventTime(BaseModel):
       timeStart: Optional[str] = Field(default=None)
       timeEnd: Optional[str] = Field(default=None)
       sunriseTimeStart: Optional[str] = Field(default=None)
       sunsetTimeEnd: Optional[str] = Field(default=None)

   class Event(BaseModel):
       id: Optional[str] = Field(default=None)
       title: Optional[str] = Field(default="")
       description: Optional[str] = Field(default="")
       url: Optional[str] = Field(default="")
       times: Optional[List[EventTime]] = Field(default_factory=list)
       dateStart: Optional[str] = Field(default=None)
       dateEnd: Optional[str] = Field(default=None)
       isRecurring: Optional[bool] = Field(default=False)
       isAllDay: Optional[bool] = Field(default=False)
       parkCode: Optional[str] = Field(default=None)
   ```

2. **Add Data Validation and Defaults:**
   ```python
   def normalize_event_data(event_data: dict) -> dict:
       """Ensure event data has all required fields with defaults"""

       defaults = {
           "url": "",
           "dateStart": None,
           "dateEnd": None,
           "isRecurring": False,
           "isAllDay": False,
           "parkCode": None,
           "times": []
       }

       # Apply defaults for missing fields
       for key, default_value in defaults.items():
           if key not in event_data or event_data[key] is None:
               event_data[key] = default_value

       # Ensure times array has proper structure
       if "times" in event_data and event_data["times"]:
           normalized_times = []
           for time_entry in event_data["times"]:
               time_defaults = {
                   "timeStart": None,
                   "timeEnd": None,
                   "sunriseTimeStart": None,
                   "sunsetTimeEnd": None
               }

               for time_key, time_default in time_defaults.items():
                   if time_key not in time_entry:
                       time_entry[time_key] = time_default

               normalized_times.append(time_entry)

           event_data["times"] = normalized_times

       return event_data
   ```

### Step 4: Testing Strategy

1. **Create Comprehensive Tests:**
   ```python
   import pytest
   from your_mcp_server import get_campgrounds, get_events

   @pytest.mark.asyncio
   async def test_get_campgrounds_validation():
       """Test that getCampgrounds handles boolean validation correctly"""
       result = await get_campgrounds(parkCode="yose", limit=2)

       assert "error" not in result
       assert "campgrounds" in result

       # Verify boolean fields are properly converted
       for campground in result["campgrounds"]:
           if "amenities" in campground:
               amenities = campground["amenities"]
               boolean_fields = ["trashRecyclingCollection", "staffOrVolunteerHostOnsite",
                               "foodStorageLockers", "cellPhoneReception"]

               for field in boolean_fields:
                   if field in amenities:
                       assert isinstance(amenities[field], bool), f"{field} should be boolean"

   @pytest.mark.asyncio
   async def test_get_events_validation():
       """Test that getEvents handles missing fields correctly"""
       result = await get_events(parkCode="yose", limit=2)

       assert "error" not in result
       assert "events" in result

       # Verify all required fields are present
       for event in result["events"]:
           required_fields = ["url", "dateStart", "dateEnd", "isRecurring", "isAllDay", "parkCode"]
           for field in required_fields:
               assert field in event, f"Missing required field: {field}"
   ```

2. **Run Tests in Loop Until Success:**
   ```bash
   # Create a test runner script
   #!/bin/bash

   echo "Starting MCP validation fix testing loop..."

   max_attempts=10
   attempt=1

   while [ $attempt -le $max_attempts ]; do
       echo "Test attempt $attempt of $max_attempts"

       # Run the specific tests
       python -m pytest tests/test_mcp_validation.py -v

       if [ $? -eq 0 ]; then
           echo "✅ All tests passed! Validation issues fixed."
           break
       else
           echo "❌ Tests failed. Analyzing errors and fixing..."

           # Run tests with detailed output to see what's still failing
           python -m pytest tests/test_mcp_validation.py -v --tb=short

           echo "Please review the errors above and make necessary fixes."
           echo "Press Enter to run tests again, or Ctrl+C to exit..."
           read
       fi

       attempt=$((attempt + 1))
   done

   if [ $attempt -gt $max_attempts ]; then
       echo "❌ Maximum attempts reached. Please review the code manually."
       exit 1
   fi
   ```

## Implementation Checklist

- [ ] **Step 1:** Identify and locate the campgrounds and events handler files
- [ ] **Step 2:** Add boolean normalization function for campgrounds
- [ ] **Step 3:** Update Pydantic models for events to make fields optional
- [ ] **Step 4:** Add data normalization for events
- [ ] **Step 5:** Create comprehensive tests for both endpoints
- [ ] **Step 6:** Run tests and fix any remaining issues
- [ ] **Step 7:** Verify both endpoints work without validation errors
- [ ] **Step 8:** Test with actual MCP client calls

## Expected Outcome

After implementing these fixes:

1. **getCampgrounds** should successfully return campground data without boolean parsing errors
2. **getEvents** should successfully return event data without missing field errors
3. All existing functionality should remain intact
4. The MCP server should pass all validation tests

## Testing Commands

Run these commands to verify the fixes:

```python
# Test getCampgrounds
result = await get_campgrounds(parkCode="yose", limit=2)
print("getCampgrounds result:", result)

# Test getEvents
result = await get_events(parkCode="yose", limit=2)
print("getEvents result:", result)
```

Both should return successful responses without validation errors.

---

**IMPORTANT:** After implementing each fix, run the tests immediately to verify the changes work. Continue in a loop of fix → test → fix until all tests pass successfully. Do not move on to the next issue until the current one is completely resolved.
