"""Handler for finding parks."""

from typing import Any, Dict

from src.api.client import NPSAPIError, get_client
from src.constants import STATE_CODES
from src.models.requests import FindParksRequest
from src.models.responses import NPSResponse, ParkData
from src.utils.error_handler import handle_not_found_error
from src.utils.formatters import format_park_data
from src.utils.logging import get_logger

logger = get_logger(__name__)


def find_parks(request: FindParksRequest) -> Dict[str, Any]:
    """
    Search for national parks by state, activity, or keyword.

    Args:
        request: FindParksRequest with search parameters

    Returns:
        Dictionary containing park search results

    Raises:
        NPSAPIError: If the API request fails
    """
    logger.info(
        "finding_parks",
        params=request.model_dump(exclude_none=True),
        message="Finding parks with search parameters",
    )

    # Validate state codes if provided
    if request.state_code:
        provided_states = [s.strip().upper() for s in request.state_code.split(",")]
        invalid_states = [
            state for state in provided_states if state not in STATE_CODES
        ]

        if invalid_states:
            logger.warning(
                "invalid_state_codes",
                invalid_states=invalid_states,
                message="Invalid state code(s) provided",
            )
            return {
                "error": f"Invalid state code(s): {', '.join(invalid_states)}",
                "validStateCodes": STATE_CODES,
            }

    # Get API client
    client = get_client()

    # Set default limit if not provided or if it exceeds maximum
    limit = min(request.limit, 50) if request.limit else 10

    # Build query parameters from request
    params = {}
    if request.state_code:
        params["stateCode"] = request.state_code
    if request.q:
        params["q"] = request.q
    params["limit"] = limit
    if request.start:
        params["start"] = request.start
    if request.activities:
        params["activities"] = request.activities

    # Make API request
    try:
        response = client.get_parks(**params)
        total_parks = int(response.get("total", 0))
        logger.info(
            "parks_found", total=total_parks, message=f"Found {total_parks} parks"
        )

        # Parse response into Pydantic models
        nps_response = NPSResponse[ParkData](**response)

        # Format the response for better readability
        formatted_parks = format_park_data(nps_response.data)

        result = {
            "total": int(nps_response.total),
            "limit": int(nps_response.limit),
            "start": int(nps_response.start),
            "parks": formatted_parks,
        }

        return result
    except NPSAPIError as e:
        logger.error("find_parks_failed", error=e.message, error_type=e.error_type)
        raise
