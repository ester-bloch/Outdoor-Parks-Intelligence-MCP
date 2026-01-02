"""Tool handlers for the National Parks MCP server."""

from src.handlers.find_parks import find_parks
from src.handlers.get_air_quality import get_air_quality
from src.handlers.get_alerts import get_alerts
from src.handlers.get_campgrounds import get_campgrounds
from src.handlers.get_events import get_events
from src.handlers.get_park_context import get_park_context
from src.handlers.get_park_details import get_park_details
from src.handlers.get_visitor_centers import get_visitor_centers
from src.handlers.get_weather import get_weather

__all__ = [
    "find_parks",
    "get_park_details",
    "get_air_quality",
    "get_alerts",
    "get_visitor_centers",
    "get_campgrounds",
    "get_events",
    "get_weather",
    "get_park_context",
]
