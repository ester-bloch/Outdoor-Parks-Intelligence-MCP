"""Handler for getting air quality data."""

from typing import Any, Dict

from src.api.air_quality import get_air_quality_client
from src.models.external import (
    AirQualityIndices,
    AirQualityLocation,
    AirQualityResponse,
)
from src.models.requests import GetAirQualityRequest
from src.utils.error_handler import handle_invalid_input_error, handle_not_found_error
from src.utils.geo import LocationResolutionError, resolve_park_location
from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_air_quality(request: GetAirQualityRequest) -> Dict[str, Any]:
    """
    Get air quality data for a location or park code.

    Args:
        request: GetAirQualityRequest with location inputs

    Returns:
        Dictionary containing air quality information

    Raises:
        AirQualityAPIError: If the API request fails
    """
    logger.info("Getting air quality data")

    park = None
    if request.park_code:
        try:
            park, latitude, longitude = resolve_park_location(request.park_code)
        except LocationResolutionError as exc:
            if exc.reason == "park_not_found":
                return handle_not_found_error("park", request.park_code)
            return handle_invalid_input_error(
                exc.message, details={"parkCode": request.park_code}
            )
    else:
        assert request.latitude is not None and request.longitude is not None
        latitude = float(request.latitude)
        longitude = float(request.longitude)

    client = get_air_quality_client()
    response = client.get_nearest_city(latitude, longitude)

    data = response.get("data", {})
    location_data = data.get("location", {}) or {}
    coordinates = location_data.get("coordinates") or [longitude, latitude]
    pollution = (data.get("current") or {}).get("pollution", {})

    result = AirQualityResponse(
        location=AirQualityLocation(
            city=data.get("city"),
            state=data.get("state"),
            country=data.get("country"),
            latitude=float(coordinates[1]),
            longitude=float(coordinates[0]),
        ),
        indices=AirQualityIndices(
            aqi_us=pollution.get("aqius"),
            aqi_cn=pollution.get("aqicn"),
            main_pollutant_us=pollution.get("mainus"),
            main_pollutant_cn=pollution.get("maincn"),
        ),
        timestamp=pollution.get("ts"),
    )

    payload = result.model_dump(exclude_none=True)
    if park:
        payload["park"] = {"name": park.full_name, "code": park.park_code}

    logger.info("Successfully retrieved air quality data")
    return payload
