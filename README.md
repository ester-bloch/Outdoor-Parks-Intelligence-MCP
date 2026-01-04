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

- **[National Park Service (NPS)](https://www.nps.gov/subjects/developer/api-documentation.htm)**
The official national data source of the United States National Park Service, providing Authoritative park data including parks, alerts, visitor centers, campgrounds, and events.
Configured via `NPS_API_KEY`.

### Weather
- **[Open-Meteo](https://open-meteo.com/en/docs)** (default; no API key required)
- **[OpenWeather](https://openweathermap.org/api)** (optional; API-key based)

Provider selection strategy:
If `OPENWEATHER_API_KEY` is configured, the server attempts OpenWeather first and falls back to Open-Meteo on provider failure.

### Air Quality
- **[IQAir / AirVisual API](https://api-docs.iqair.com/)**

Provides AQI and pollutant data. Requires `AIRVISUAL_API_KEY`.
If the key is not configured, air-quality requests return a structured configuration error.

---

## MCP Tools


### Park & Location Tools

- #### `findParks`
Search parks by state, keywords, and activities.

#### `getParkDetails`
Retrieve a full park profile.

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

All tools:
- Validate inputs using Pydantic models
- Return structured JSON only
- Surface errors in a consistent machine-readable format
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

### API Keys

1. Generate API keys from:
- **`NPS_API_KEY` (required)** — [National Park Service](https://www.nps.gov/subjects/developer/get-started.htm)
- **`OPENWEATHER_API_KEY` (optional)** — [OpenWeather](https://openweathermap.org/appid)
- **`AIRVISUAL_API_KEY` (optional)** — [IQAir / AirVisual](https://www.iqair.com/support/knowledge-base/KA-04891-INTL)


2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and set the configuration values:
   ```dotenv
   # Required
   NPS_API_KEY=your_nps_api_key_here

   # Optional (enable air quality)
   AIRVISUAL_API_KEY=your_airvisual_api_key_here

   # Optional (prefer OpenWeather; otherwise Open-Meteo is used)
   OPENWEATHER_API_KEY=your_openweather_api_key_here
---


### Run the server using Poetry

```bash
poetry run python -m src.main
```

### Run using venv

```bash
python -m src.main
```

The server runs over **stdio**, per MCP conventions.

---

## Development and Testing

### Running Tests

```bash
poetry run pytest
poetry run pytest --cov=src --cov-report=html
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/property/
```

### Code Quality

```bash
poetry run black src tests
poetry run isort src tests
poetry run flake8 src tests
poetry run mypy src
```

### Pre-commit Hooks

```bash
pre-commit run --all-files
pre-commit run black
pre-commit run mypy
```

---

## Error Model

All errors are returned as structured JSON objects and categorized as:
- Input validation errors
- Missing or invalid configuration
- Upstream provider HTTP errors
- Network and timeout failures

No free-text or implicit error responses are produced.

---

## Project Structure

```text
developer 2/
├── docs/
│   └── claude_desktop_config.json
├── scripts/
│   └── demo.py
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── air_quality.py
│   │   ├── client.py
│   │   ├── rate_limit.py
│   │   ├── retry.py
│   │   └── weather.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── find_parks.py
│   │   ├── get_air_quality.py
│   │   ├── get_alerts.py
│   │   ├── get_campgrounds.py
│   │   ├── get_events.py
│   │   ├── get_park_context.py
│   │   ├── get_park_details.py
│   │   ├── get_visitor_centers.py
│   │   └── get_weather.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── external.py
│   │   ├── requests.py
│   │   └── responses.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── error_handler.py
│   │   ├── formatters.py
│   │   ├── geo.py
│   │   └── logging.py
│   ├── __init__.py
│   ├── config.py
│   ├── constants.py
│   ├── main.py
│   └── server.py
├── tests/
│   ├── integration/
│   │   ---
│   ├── property/
│   │   ---
│   ├── unit/
│   │   ---
│   ├── __init__.py
│   └── conftest.py
├── .env.example
├── .flake8
├── .gitignore
├── .pre-commit-config.yaml
├── poetry.lock
├── pyproject.toml
├── requirements-dev.txt
└── requirements.txt
```

Key conventions:
- `src/api/` contains provider clients plus resilience primitives (retry / rate limit).
- `src/handlers/` contains the MCP tool implementations (one file per tool).
- `src/models/` defines request/response schemas and the normalized error model.
- `tests/` is split by test intent (unit / integration / property).
- Generated artifacts (e.g., `__pycache__/`, `*.pyc`) are development by-products and should not be versioned.

---

## Extending

### Add a Provider
1. Implement the client in `src/api/`
2. Register configuration keys in `.env.example`
3. Integrate via a handler without cross-provider coupling

### Add a Tool
1. Implement logic in `src/handlers/`
2. Define schemas in `src/models/`
3. Register the tool in `server.py`

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request

---

## Acknowledgments

- Built with **[FastMCP](https://github.com/jlowin/fastmcp)**
- Data provided by:
  - **[National Park Service API](https://www.nps.gov/subjects/developer/)**
  - **[Open-Meteo](https://open-meteo.com/en/docs)**
  - **[OpenWeather](https://openweathermap.org/api)**
  - **[IQAir / AirVisual](https://api-docs.iqair.com/)**
