"""Unit tests for external data handlers."""

from unittest.mock import Mock, patch

from src.handlers.get_air_quality import get_air_quality
from src.handlers.get_park_context import get_park_context
from src.handlers.get_weather import get_weather
from src.models.requests import (
    GetAirQualityRequest,
    GetParkContextRequest,
    GetWeatherRequest,
)


def test_get_air_quality_coordinates_success():
    mock_response = {
        "status": "success",
        "data": {
            "city": "Sample City",
            "state": "Sample State",
            "country": "Sample Country",
            "location": {"coordinates": [-119.5, 37.8]},
            "current": {
                "pollution": {
                    "aqius": 42,
                    "aqicn": 50,
                    "mainus": "pm25",
                    "maincn": "pm10",
                    "ts": "2024-01-01T00:00:00.000Z",
                }
            },
        },
    }

    with patch("src.handlers.get_air_quality.get_air_quality_client") as mock_client:
        mock_client.return_value.get_nearest_city.return_value = mock_response
        request = GetAirQualityRequest(latitude=37.8, longitude=-119.5)
        result = get_air_quality(request)

        assert result["provider"] == "airvisual"
        assert result["location"]["city"] == "Sample City"
        assert result["indices"]["aqi_us"] == 42


def test_get_weather_open_meteo_success():
    mock_response = {
        "latitude": 37.8,
        "longitude": -119.5,
        "current_weather": {
            "temperature": 22.5,
            "windspeed": 4.2,
            "winddirection": 90,
            "time": "2024-01-01T00:00",
        },
    }

    with patch("src.handlers.get_weather.get_open_meteo_client") as mock_client:
        mock_client.return_value.get_current_weather.return_value = mock_response
        request = GetWeatherRequest(
            latitude=37.8, longitude=-119.5, provider="open-meteo"
        )
        result = get_weather(request)

        assert result["provider"] == "open-meteo"
        assert result["temperature_c"] == 22.5


def test_get_park_context_success():
    mock_air_response = {
        "status": "success",
        "data": {
            "city": "Sample City",
            "state": "Sample State",
            "country": "Sample Country",
            "location": {"coordinates": [-119.5, 37.8]},
            "current": {
                "pollution": {
                    "aqius": 42,
                    "aqicn": 50,
                    "mainus": "pm25",
                    "maincn": "pm10",
                    "ts": "2024-01-01T00:00:00.000Z",
                }
            },
        },
    }
    mock_weather_response = {
        "latitude": 37.8,
        "longitude": -119.5,
        "current_weather": {
            "temperature": 22.5,
            "windspeed": 4.2,
            "winddirection": 90,
            "time": "2024-01-01T00:00",
        },
    }

    mock_park = Mock()
    mock_park.full_name = "Sample Park"
    mock_park.park_code = "samp"
    mock_park.url = "https://example.com"

    with patch("src.handlers.get_park_context.resolve_park_location") as mock_resolver:
        with patch("src.handlers.get_park_context.get_air_quality_client") as mock_air:
            with patch(
                "src.handlers.get_park_context.get_open_meteo_client"
            ) as mock_weather:
                mock_resolver.return_value = (mock_park, 37.8, -119.5)
                mock_air.return_value.get_nearest_city.return_value = mock_air_response
                mock_weather.return_value.get_current_weather.return_value = (
                    mock_weather_response
                )

                request = GetParkContextRequest(
                    park_code="samp", weather_provider="open-meteo"
                )
                result = get_park_context(request)

                assert result["park"]["code"] == "samp"
                assert result["airQuality"]["provider"] == "airvisual"
                assert result["weather"]["provider"] == "open-meteo"
