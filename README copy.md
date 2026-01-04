# National Parks Intelligence MCP Server

An implementation of a Model Context Protocol (MCP) server in Python, providing structured access to U.S. National Parks data combined with environmental information such as weather conditions and air quality.

The server exposes a set of MCP tools that allow MCP-compatible clients to query park data, alerts, facilities, events, and related environmental context through a unified and typed interface.

## Overview

This project implements an MCP server using the Python MCP SDK and FastMCP.
It integrates multiple external data providers and exposes them as discrete MCP tools with consistent schemas, validation, and error handling.

Primary capabilities include:
- Querying National Park Service (NPS) data
- Retrieving real-time weather information
- Retrieving air quality metrics
- Aggregating multiple data sources into a single contextual response

## Architecture

The server follows a modular structure separating transport, business logic, provider access, and data models.

src/
  server.py              MCP server initialization and tool registration
  handlers/              Tool-level business logic
  api/                   External API clients
  models/                Pydantic request and response models
  utils/                 Logging and error-handling utilities

tests/
  unit/
  integration/
  property/

docs/
  claude_desktop_config.json

All external requests are executed asynchronously.
Input and output schemas are validated using Pydantic.
Errors originating from external providers are normalized before being returned to MCP clients.

## MCP Tools

findParks
Search for national parks using filters such as state code, free-text query, activities, and pagination parameters.

getParkDetails
Retrieve detailed information for a specific park using its parkCode.

getAlerts
Return active alerts for a given park, with optional filtering and pagination.

getVisitorCenters
Retrieve visitor center information associated with a park.

getCampgrounds
Retrieve campground information associated with a park.

getEvents
Query events for a park, optionally filtered by date range and search terms.

getWeather
Retrieve current weather data for a geographic location specified by latitude and longitude.

getAirQuality
Retrieve air quality data for a geographic location specified by latitude and longitude.

getParkContext
Return a combined response including park details, current weather, and current air quality.

## Requirements

Python 3.10 or later
Poetry (recommended) or pip

## Installation

Using Poetry:

poetry install
poetry run python-mcp-nationalparks

Using pip:

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main

## Configuration

Required environment variables:
- NPS_API_KEY
- AIRVISUAL_API_KEY

Optional:
- OPENWEATHER_API_KEY

A reference configuration is provided in .env.example.

## MCP Client Integration

A sample configuration for Claude Desktop is available in:

docs/claude_desktop_config.json

## Testing

The test suite includes unit, integration, and property-based tests.

Run all tests:

poetry run pytest

## License

See the license file included in the repository.
