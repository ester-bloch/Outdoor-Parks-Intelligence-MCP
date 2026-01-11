"""Handler for getting weather data."""

from datetime import datetime, timezone
from typing import Any, Dict

from src.api.weather import (
    WeatherAPIError,
    get_open_meteo_client,
    get_openweather_client,
)
from src.config import settings
from src.models.external import WeatherResponse
from src.models.requests import GetWeatherRequest
from src.utils.error_handler import handle_invalid_input_error, handle_not_found_error
from src.utils.geo import LocationResolutionError, resolve_park_location
from src.utils.logging import get_logger

logger = get_logger(__name__)

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


def get_weather(request: GetWeatherRequest) -> Dict[str, Any]:
    """
    Get weather data for a location or park code.

    Args:
        request: GetWeatherRequest with location inputs

    Returns:
        Dictionary containing weather information

    Raises:
        WeatherAPIError: If the API request fails
    """
    logger.info("Getting weather data")

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

    provider = (request.provider or "auto").lower()
    if provider not in _ALLOWED_PROVIDERS:
        return handle_invalid_input_error(
            "Unsupported weather provider",
            details={"provider": request.provider},
        )

    if provider == "openweather":
        client = get_openweather_client()
        response = client.get_current_weather(latitude, longitude)
        result = _build_openweather_response(response)
    elif provider in {"open-meteo", "open_meteo"}:
        client = get_open_meteo_client()
        response = client.get_current_weather(latitude, longitude)
        result = _build_open_meteo_response(response)
    else:
        if settings.openweather_api_key:
            try:
                client = get_openweather_client()
                response = client.get_current_weather(latitude, longitude)
                result = _build_openweather_response(response)
            except WeatherAPIError as exc:
                logger.warning(
                    "openweather_failed_fallback",
                    error=exc.message,
                    status_code=exc.status_code,
                )
                client = get_open_meteo_client()
                response = client.get_current_weather(latitude, longitude)
                result = _build_open_meteo_response(response)
        else:
            client = get_open_meteo_client()
            response = client.get_current_weather(latitude, longitude)
            result = _build_open_meteo_response(response)

    payload = result.model_dump(exclude_none=True)
    if park:
        payload["park"] = {"name": park.full_name, "code": park.park_code}

    logger.info("Successfully retrieved weather data")
    return payload
