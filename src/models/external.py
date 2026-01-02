"""Pydantic models for external data sources."""

from typing import Optional

from pydantic import BaseModel, Field


class AirQualityLocation(BaseModel):
    """Location details for air quality responses."""

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: float
    longitude: float


class AirQualityIndices(BaseModel):
    """Air quality index values and pollutants."""

    aqi_us: Optional[int] = Field(None, description="US AQI value")
    aqi_cn: Optional[int] = Field(None, description="China AQI value")
    main_pollutant_us: Optional[str] = Field(
        None, description="Main pollutant for US AQI"
    )
    main_pollutant_cn: Optional[str] = Field(
        None, description="Main pollutant for China AQI"
    )


class AirQualityResponse(BaseModel):
    """Normalized air quality response."""

    provider: str = Field(default="airvisual")
    location: AirQualityLocation
    indices: AirQualityIndices
    timestamp: Optional[str] = Field(None, description="Observation timestamp")


class WeatherResponse(BaseModel):
    """Normalized weather response."""

    provider: str
    latitude: float
    longitude: float
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    pressure_hpa: Optional[float] = None
    wind_speed_m_s: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    weather_description: Optional[str] = None
    observation_time: Optional[str] = None
