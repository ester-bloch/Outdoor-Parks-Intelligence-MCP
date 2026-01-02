"""Handler for combined park context data."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from src.api.air_quality import get_air_quality_client
from src.api.weather import (
    WeatherAPIError,
    get_open_meteo_client,
    get_openweather_client,
)
from src.config import settings
from src.models.external import (
    AirQualityIndices,
    AirQualityLocation,
    AirQualityResponse,
    WeatherResponse,
)
from src.models.requests import GetParkContextRequest
from src.utils.error_handler import handle_invalid_input_error, handle_not_found_error
from src.utils.geo import LocationResolutionError, resolve_park_location

logger = logging.getLogger(__name__)

_ALLOWED_PROVIDERS = {"auto", "openweather", "open-meteo", "open_meteo"}


def _format_openweather_time(timestamp: int | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _build_openweather_response(data: Dict[str, Any]) -> WeatherResponse:
    weather_desc = None
    if data.get("weather"):
        weather_desc = data["weather"][0].get("description")

    return WeatherResponse(
        provider="openweather",
        latitude=float(data.get("coord", {}).get("lat")),
        longitude=float(data.get("coord", {}).get("lon")),
        temperature_c=(data.get("main") or {}).get("temp"),
        humidity_percent=(data.get("main") or {}).get("humidity"),
        pressure_hpa=(data.get("main") or {}).get("pressure"),
        wind_speed_m_s=(data.get("wind") or {}).get("speed"),
        wind_direction_deg=(data.get("wind") or {}).get("deg"),
        weather_description=weather_desc,
        observation_time=_format_openweather_time(data.get("dt")),
    )


def _build_open_meteo_response(data: Dict[str, Any]) -> WeatherResponse:
    current = data.get("current_weather") or {}
    return WeatherResponse(
        provider="open-meteo",
        latitude=float(data.get("latitude")),
        longitude=float(data.get("longitude")),
        temperature_c=current.get("temperature"),
        wind_speed_m_s=current.get("windspeed"),
        wind_direction_deg=current.get("winddirection"),
        observation_time=current.get("time"),
    )


def get_park_context(request: GetParkContextRequest) -> Dict[str, Any]:
    """
    Get combined park context (NPS + weather + air quality).

    Args:
        request: GetParkContextRequest with park code

    Returns:
        Dictionary containing park context data

    Raises:
        AirQualityAPIError: If air quality request fails
        WeatherAPIError: If weather request fails
    """
    logger.info("Getting park context", park_code=request.park_code)

    try:
        park, latitude, longitude = resolve_park_location(request.park_code)
    except LocationResolutionError as exc:
        if exc.reason == "park_not_found":
            return handle_not_found_error("park", request.park_code)
        return handle_invalid_input_error(
            exc.message, details={"parkCode": request.park_code}
        )

    provider = (request.weather_provider or "auto").lower()
    if provider not in _ALLOWED_PROVIDERS:
        return handle_invalid_input_error(
            "Unsupported weather provider",
            details={"provider": request.weather_provider},
        )

    air_client = get_air_quality_client()
    air_response = air_client.get_nearest_city(latitude, longitude)
    air_data = air_response.get("data", {})
    location_data = air_data.get("location", {}) or {}
    coordinates = location_data.get("coordinates") or [longitude, latitude]
    pollution = (air_data.get("current") or {}).get("pollution", {})

    air_quality = AirQualityResponse(
        location=AirQualityLocation(
            city=air_data.get("city"),
            state=air_data.get("state"),
            country=air_data.get("country"),
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
    ).model_dump(exclude_none=True)

    if provider == "openweather":
        weather_client = get_openweather_client()
        weather_raw = weather_client.get_current_weather(latitude, longitude)
        weather = _build_openweather_response(weather_raw).model_dump(exclude_none=True)
    elif provider in {"open-meteo", "open_meteo"}:
        weather_client = get_open_meteo_client()
        weather_raw = weather_client.get_current_weather(latitude, longitude)
        weather = _build_open_meteo_response(weather_raw).model_dump(exclude_none=True)
    else:
        if settings.openweather_api_key:
            try:
                weather_client = get_openweather_client()
                weather_raw = weather_client.get_current_weather(latitude, longitude)
                weather = _build_openweather_response(weather_raw).model_dump(
                    exclude_none=True
                )
            except WeatherAPIError as exc:
                logger.warning(
                    "openweather_failed_fallback",
                    error=exc.message,
                    status_code=exc.status_code,
                )
                weather_client = get_open_meteo_client()
                weather_raw = weather_client.get_current_weather(latitude, longitude)
                weather = _build_open_meteo_response(weather_raw).model_dump(
                    exclude_none=True
                )
        else:
            weather_client = get_open_meteo_client()
            weather_raw = weather_client.get_current_weather(latitude, longitude)
            weather = _build_open_meteo_response(weather_raw).model_dump(
                exclude_none=True
            )

    payload = {
        "park": {
            "name": park.full_name,
            "code": park.park_code,
            "url": park.url,
            "location": {"latitude": latitude, "longitude": longitude},
        },
        "airQuality": air_quality,
        "weather": weather,
    }

    logger.info("Successfully retrieved park context", park_code=park.park_code)
    return payload
