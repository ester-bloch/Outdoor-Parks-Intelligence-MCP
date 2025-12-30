"""Handler for getting visitor center information."""

import logging
from typing import Any, Dict

from src.api.client import NPSAPIError, get_client
from src.models.requests import GetVisitorCentersRequest
from src.models.responses import NPSResponse, VisitorCenterData
from src.utils.formatters import format_visitor_center_data

logger = logging.getLogger(__name__)


def get_visitor_centers(request: GetVisitorCentersRequest) -> Dict[str, Any]:
    """
    Get visitor center information for national parks.

    Args:
        request: GetVisitorCentersRequest with search parameters

    Returns:
        Dictionary containing visitor center data

    Raises:
        NPSAPIError: If the API request fails
    """
    logger.info(
        f"Getting visitor centers with params: {request.model_dump(exclude_none=True)}"
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
        response = client.get_visitor_centers(**params)
        logger.info(f"Found {response.get('total', 0)} visitor centers")

        # Parse response into Pydantic models
        nps_response = NPSResponse[VisitorCenterData](**response)

        # Format the response for better readability
        formatted_centers = format_visitor_center_data(nps_response.data)

        # Group visitor centers by park code for better organization
        centers_by_park: Dict[str, list] = {}
        for center in formatted_centers:
            park_code = center["parkCode"]
            if park_code not in centers_by_park:
                centers_by_park[park_code] = []
            centers_by_park[park_code].append(center)

        result = {
            "total": int(nps_response.total),
            "limit": int(nps_response.limit),
            "start": int(nps_response.start),
            "visitorCenters": formatted_centers,
            "visitorCentersByPark": centers_by_park,
        }

        return result
    except NPSAPIError as e:
        logger.error(f"Failed to get visitor centers: {e.message}")
        raise
