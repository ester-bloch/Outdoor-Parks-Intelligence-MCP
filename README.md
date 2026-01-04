# Outdoor & Parks Intelligence MCP Server

A **Model Context Protocol (MCP)** server that exposes structured outdoor intelligence through typed tools.
The server aggregates data from multiple external providers (parks, weather, air quality), validates inputs and outputs, and returns deterministic JSON responses suitable for automated and human evaluation.

The server acts as a controlled execution layer between language models and external environmental data providers, enforcing strict contracts, predictable behavior, and operational safeguards such as retries, rate limiting, and error normalization.

---

## Scope

This MCP server provides a unified interface for:

- National park and location metadata
- Safety and operational alerts
- Environmental conditions (weather, air quality)
- Contextual summaries derived from multiple data sources

All functionality is exposed via MCP tools with strict input/output schemas.

---

## Data Providers

### [National Park Service (NPS)](https://www.nps.gov/subjects/developer/api-documentation.htm)
Authoritative park data including parks, alerts, visitor centers, campgrounds, and events.

Configured via `NPS_API_KEY`.

### Weather
Provider selection strategy:
- **[Open-Meteo](https://open-meteo.com/en/docs)** (default; no API key required)
- **[OpenWeather](https://openweathermap.org/api)** (optional; API-key based)

If `OPENWEATHER_API_KEY` is configured, the server attempts OpenWeather first and falls back to Open-Meteo on provider failure.

### Air Quality
- **[IQAir / AirVisual API](https://api-docs.iqair.com/)**

Provides AQI and pollutant data. Requires `AIRVISUAL_API_KEY`.
If the key is not configured, air-quality requests return a structured configuration error.

---

## MCP Tools

All tools:
- Validate inputs using Pydantic models
- Return structured JSON only
- Surface errors in a consistent machine-readable format

### Park & Location Tools

#### `findParks`
Search parks by state, keywords, and activities.

#### `getParkDetails`
Retrieve a normalized park profile.

#### `getVisitorCenters`
Retrieve visitor center data for a park.

#### `getCampgrounds`
Retrieve campground data for a park.

#### `getEvents`
Retrieve park-related events.

### Safety & Context Tools

#### `getAlerts`
Retrieve active alerts and warnings.

#### `getParkContext`
Return a condensed context object combining park metadata, alerts, and safety information.

### Environmental Tools

#### `getWeather`
Retrieve live weather conditions.

#### `getAirQuality`
Retrieve air-quality indices and pollutant data.

---

## Installation

### Prerequisites
- Python **3.10+**
- Poetry (recommended) or pip

### Poetry

```bash
git clone https://github.com/ester-bloch/Outdoor-Parks-Intelligence-MCP.git
cd Outdoor-Parks-Intelligence-MCP
poetry install
```

### pip / venv

```bash
git clone https://github.com/ester-bloch/Outdoor-Parks-Intelligence-MCP.git
cd Outdoor-Parks-Intelligence-MCP
python -m venv .venv
pip install -e .
```

---

## Configuration

- **`NPS_API_KEY` (required)** — [National Park Service](https://www.nps.gov/subjects/developer/get-started.htm)
- **`OPENWEATHER_API_KEY` (optional)** — [OpenWeather](https://openweathermap.org/appid)
- **`AIRVISUAL_API_KEY` (optional)** — [IQAir / AirVisual](https://www.iqair.com/support/knowledge-base/KA-04891-INTL)

---

## Usage

```bash
python -m src.main
```

The server runs over **stdio**, per MCP conventions.

---

## Acknowledgments

- Built with **[FastMCP](https://github.com/jlowin/fastmcp)**
- Data provided by:
  - **[National Park Service API](https://www.nps.gov/subjects/developer/)**
  - **[Open-Meteo](https://open-meteo.com/en/docs)**
  - **[OpenWeather](https://openweathermap.org/api)**
  - **[IQAir / AirVisual](https://api-docs.iqair.com/)**
