"""Handler for getting campground information."""

from typing import Any, Dict

from pydantic import ValidationError

import src.api.client as nps_client
from src.models.requests import GetCampgroundsRequest
from src.models.responses import CampgroundData, NPSResponse
from src.utils.formatters import format_campground_data
from src.utils.logging import get_logger

get_client = nps_client.get_client

logger = get_logger(__name__)


def get_campgrounds(request: GetCampgroundsRequest) -> Dict[str, Any]:
    """
    Get campground information for national parks.

    Args:
        request: GetCampgroundsRequest with search parameters

    Returns:
        Dictionary containing campground data

    Raises:
        NPSAPIError: If the API request fails
    """
    logger.info(
        f"Getting campgrounds with params: {request.model_dump(exclude_none=True)}"
    )

    # Get API client
    client = get_client()

    # Set default limit if not provided or if it exceeds maximum
    limit = min(request.limit, 50) if request.limit else 10

    # Build query parameters from request
    params = {"limit": limit}
    if request.park_code:
        params["parkCode"] = request.park_code
    if request.start:
        params["start"] = request.start
    if request.q:
        params["q"] = request.q

    # Make API request
    try:
        response = client.get_campgrounds(**params)
        logger.info(f"Found {response.get('total', 0)} campgrounds")

        # Parse response items individually with graceful error handling
        validated_data = []
        for item in response.get("data", []):
            try:
                validated_item = CampgroundData.model_validate(item)
                validated_data.append(validated_item)
            except ValidationError as e:
                logger.warning(
                    f"Validation error for campground {item.get('name', 'unknown')}: {e}"
                )
                continue

        # Create response with validated items and ensure metadata is always present
        nps_response = NPSResponse[CampgroundData](
            total=response.get("total", str(len(validated_data))),
            limit=response.get("limit", str(limit)),
            start=response.get("start", "0"),
            data=validated_data,
        )

        # Format the response for better readability
        formatted_campgrounds = format_campground_data(nps_response.data)

        # Group campgrounds by park code for better organization
        campgrounds_by_park: Dict[str, list] = {}
        for campground in formatted_campgrounds:
            park_code = campground["parkCode"]
            if park_code not in campgrounds_by_park:
                campgrounds_by_park[park_code] = []
            campgrounds_by_park[park_code].append(campground)

        result = {
            "total": int(nps_response.total),
            "limit": int(nps_response.limit),
            "start": int(nps_response.start),
            "campgrounds": formatted_campgrounds,
            "campgroundsByPark": campgrounds_by_park,
        }

        return result
    except nps_client.NPSAPIError as e:
        logger.error(f"Failed to get campgrounds: {e.message}")
        raise
