"""Handler for getting park alerts and closures."""

from typing import Any, Dict

import src.api.client as nps_client
from src.models.requests import GetAlertsRequest
from src.models.responses import AlertData, NPSResponse
from src.utils.formatters import format_alert_data
from src.utils.logging import get_logger

get_client = nps_client.get_client
logger = get_logger(__name__)


def get_alerts(request: GetAlertsRequest) -> Dict[str, Any]:
    """
    Get current alerts, closures, and important notices for national parks.

    Args:
        request: GetAlertsRequest with search parameters

    Returns:
        Dictionary containing alert data

    Raises:
        NPSAPIError: If the API request fails
    """
    logger.info(f"Getting alerts with params: {request.model_dump(exclude_none=True)}")

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
        response = client.get_alerts(**params)
        logger.info(f"Found {response.get('total', 0)} alerts")

        # Parse response into Pydantic models
        nps_response = NPSResponse[AlertData](**response)

        # Format the response for better readability
        formatted_alerts = format_alert_data(nps_response.data)

        # Group alerts by park code for better organization
        alerts_by_park: Dict[str, list] = {}
        for alert in formatted_alerts:
            park_code = alert["parkCode"]
            if park_code not in alerts_by_park:
                alerts_by_park[park_code] = []
            alerts_by_park[park_code].append(alert)

        result = {
            "total": int(nps_response.total),
            "limit": int(nps_response.limit),
            "start": int(nps_response.start),
            "alerts": formatted_alerts,
            "alertsByPark": alerts_by_park,
        }

        return result
    except nps_client.NPSAPIError as e:
        logger.error(f"Failed to get alerts: {e.message}")
        raise
