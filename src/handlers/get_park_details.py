"""Handler for getting detailed park information."""

import logging
from typing import Any, Dict

from src.api.client import NPSAPIError, get_client
from src.models.requests import GetParkDetailsRequest
from src.models.responses import NPSResponse, ParkData
from src.utils.error_handler import handle_not_found_error
from src.utils.formatters import format_park_details

logger = logging.getLogger(__name__)


def get_park_details(request: GetParkDetailsRequest) -> Dict[str, Any]:
    """
    Get comprehensive information about a specific national park.

    Args:
        request: GetParkDetailsRequest with park code

    Returns:
        Dictionary containing detailed park information

    Raises:
        NPSAPIError: If the API request fails
    """
    logger.info(f"Getting park details for park code: {request.park_code}")

    # Get API client
    client = get_client()

    # Make API request using park code
    try:
        response = client.get_park_by_code(request.park_code)
        logger.debug(f"Received response for park code: {request.park_code}")

        # Check if park was found
        if not response.get("data") or len(response["data"]) == 0:
            logger.warning(f"No park found with park code: {request.park_code}")
            return handle_not_found_error("park", request.park_code)

        # Parse response into Pydantic model
        nps_response = NPSResponse[ParkData](**response)

        # Format the park details for better readability
        park_details = format_park_details(nps_response.data[0])

        logger.info(f"Successfully retrieved details for park: {park_details['name']}")
        return park_details

    except NPSAPIError as e:
        logger.error(f"Failed to get park details: {e.message}")
        raise
