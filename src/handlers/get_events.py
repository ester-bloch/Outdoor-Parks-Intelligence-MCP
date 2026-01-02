"""Handler for getting park events and programs."""

import logging
from typing import Any, Dict

import src.api.client as nps_client
from src.models.requests import GetEventsRequest
from src.models.responses import EventData, NPSResponse
from src.utils.formatters import format_event_data

get_client = nps_client.get_client
logger = logging.getLogger(__name__)


def get_events(request: GetEventsRequest) -> Dict[str, Any]:
    """
    Get park events and programs.

    Args:
        request: GetEventsRequest with search parameters

    Returns:
        Dictionary containing event data

    Raises:
        NPSAPIError: If the API request fails
    """
    logger.info(f"Getting events with params: {request.model_dump(exclude_none=True)}")

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
    if request.date_start:
        params["dateStart"] = request.date_start
    if request.date_end:
        params["dateEnd"] = request.date_end

    # Make API request
    try:
        response = client.get_events(**params)
        logger.info(f"Found {response.get('total', 0)} events")

        # Parse response into Pydantic models
        nps_response = NPSResponse[EventData](**response)

        # Format the response for better readability
        formatted_events = format_event_data(nps_response.data)

        # Group events by park code for better organization
        events_by_park: Dict[str, list] = {}
        for event in formatted_events:
            park_code = event["parkCode"]
            if park_code not in events_by_park:
                events_by_park[park_code] = []
            events_by_park[park_code].append(event)

        result = {
            "total": int(nps_response.total),
            "limit": int(nps_response.limit),
            "start": int(nps_response.start),
            "events": formatted_events,
            "eventsByPark": events_by_park,
        }

        return result
    except nps_client.NPSAPIError as e:
        logger.error(f"Failed to get events: {e.message}")
        raise
