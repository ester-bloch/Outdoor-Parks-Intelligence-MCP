"""Geospatial helpers for resolving park coordinates."""

from typing import Tuple

import src.api.client as nps_client
from src.models.responses import NPSResponse, ParkData


class LocationResolutionError(Exception):
    """Raised when a park location cannot be resolved."""

    def __init__(self, message: str, reason: str):
        """
        Initialize location resolution error.

        Args:
            message: Error message
            reason: Reason for the error
        """
        self.message = message
        self.reason = reason
        super().__init__(message)


def resolve_park_location(park_code: str) -> Tuple[ParkData, float, float]:
    """
    Resolve a park code into a ParkData model and coordinates.

    Args:
        park_code: NPS park code

    Returns:
        Tuple of (ParkData, latitude, longitude)
    """
    client = nps_client.get_client()
    response = client.get_park_by_code(park_code)
    if not response.get("data"):
        raise LocationResolutionError(
            message=f"No park found with park code: {park_code}",
            reason="park_not_found",
        )

    nps_response = NPSResponse[ParkData](**response)
    park = nps_response.data[0]

    try:
        latitude = float(park.latitude)
        longitude = float(park.longitude)
    except (TypeError, ValueError):
        raise LocationResolutionError(
            message=f"Missing or invalid coordinates for park code: {park_code}",
            reason="invalid_coordinates",
        )

    return park, latitude, longitude
