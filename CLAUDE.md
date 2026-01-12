# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Outdoor & Parks Intelligence MCP Server** that exposes structured outdoor intelligence through typed tools via the Model Context Protocol (MCP). It aggregates data from multiple external providers (National Park Service, weather, air quality) with strict input/output contracts, predictable behavior, and operational safeguards including retries, rate limiting, and error normalization.

Built with **FastMCP** and runs over **stdio** transport per MCP conventions.

## Development Commands

### Setup

```bash
# Using Poetry (recommended)
poetry install

# Using pip/venv
python -m venv .venv
pip install -e .
```

### Running the Server

```bash
# With Poetry
poetry run python -m src.main

# With venv
python -m src.main

# With debug logging
poetry run python -m src.main --log-level DEBUG

# With JSON formatted logs
poetry run python -m src.main --log-json
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage report
poetry run pytest --cov=src --cov-report=html

# Run specific test suites
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/property/

# Run a single test file
poetry run pytest tests/unit/test_specific.py

# Run a specific test
poetry run pytest tests/unit/test_specific.py::test_function_name
```

### Code Quality

```bash
# Format code
poetry run black src tests
poetry run isort src tests

# Lint
poetry run flake8 src tests

# Type checking
poetry run mypy src

# Run pre-commit hooks
pre-commit run --all-files
pre-commit run black
pre-commit run mypy
```

## Architecture

### High-Level Design

The codebase follows a **layered architecture** with clear separation of concerns:

1. **Transport Layer** ([src/main.py](src/main.py), [src/server.py](src/server.py))
   - FastMCP server initialization and tool registration
   - Stdio transport handling
   - Top-level error handling and logging

2. **Handler Layer** ([src/handlers/](src/handlers/))
   - One handler per MCP tool (e.g., `find_parks.py`, `get_weather.py`)
   - Business logic coordination
   - Orchestrates multiple API calls when needed (e.g., `get_park_context.py` combines NPS + weather + air quality)

3. **API Client Layer** ([src/api/](src/api/))
   - Provider-specific clients (`client.py` for NPS, `weather.py`, `air_quality.py`)
   - Resilience primitives: `retry.py` (exponential backoff), `rate_limit.py` (token bucket)
   - HTTP communication via HTTPX with automatic retries and rate limiting

4. **Model Layer** ([src/models/](src/models/))
   - Pydantic schemas for request/response validation
   - Normalized error models (`errors.py`)
   - External provider response models (`external.py`)

5. **Utility Layer** ([src/utils/](src/utils/))
   - Structured logging (`logging.py` with structlog)
   - Error handler helpers (`error_handler.py`)
   - Geographic utilities (`geo.py` for location resolution)
   - Response formatters (`formatters.py`)

### Key Architectural Patterns

**Error Handling**: All errors are normalized to structured JSON via `ErrorResponse` models. The system categorizes errors as validation, configuration, HTTP, network, or timeout failures. Custom exceptions (`NPSAPIError`, `WeatherAPIError`, `AirQualityAPIError`) convert to `ErrorResponse` models consistently.

**Resilience**: API clients wrap HTTPX clients with `RetryableHTTPClient` (exponential backoff) and `RateLimiter` (token bucket algorithm). Retries trigger on network errors, timeouts, and specific HTTP status codes (429, 500-504).

**Provider Abstraction**: Weather provider selection supports OpenWeather (API-key based) and Open-Meteo (no key required). The system attempts OpenWeather first if configured, then falls back to Open-Meteo on failure. Air quality requires IQAir/AirVisual API key; returns structured configuration error if missing.

**Tool Registration Pattern**: Each MCP tool is registered in [src/server.py](src/server.py) as a FastMCP decorator with type-annotated parameters. The decorator converts camelCase MCP parameters to snake_case Python parameters, validates via Pydantic request models, calls the handler function, and applies structured error handling.

**Location Resolution**: The `resolve_park_location()` utility in [src/utils/geo.py](src/utils/geo.py) resolves park codes to coordinates by querying the NPS API and extracting lat/lon from the park data. This is used by weather and air quality tools when a `parkCode` is provided instead of explicit coordinates.

## Configuration

Required environment variables (set in `.env`):
- `NPS_API_KEY` - National Park Service API key (required for most functionality)

Optional environment variables:
- `AIRVISUAL_API_KEY` - IQAir/AirVisual API key (enables air quality tools)
- `OPENWEATHER_API_KEY` - OpenWeather API key (preferred weather provider)

See [.env.example](.env.example) for full configuration options.

## Testing Strategy

- **Unit tests** ([tests/unit/](tests/unit/)) - Test individual functions/classes in isolation with mocked dependencies
- **Integration tests** ([tests/integration/](tests/integration/)) - Test API client integrations with real or stubbed HTTP responses
- **Property tests** ([tests/property/](tests/property/)) - Use Hypothesis for property-based testing of data transformations

Test configuration is in [pyproject.toml](pyproject.toml) under `[tool.pytest.ini_options]`.

## Adding New Functionality

### Adding a New Provider

1. Create client in [src/api/](src/api/) (e.g., `new_provider.py`)
2. Define custom exception (e.g., `NewProviderAPIError`)
3. Wrap HTTPX client with retry and rate limiting
4. Register API keys in [.env.example](.env.example) and [src/config.py](src/config.py)

### Adding a New Tool

1. Define request schema in [src/models/requests.py](src/models/requests.py)
2. Define response schema in [src/models/responses.py](src/models/responses.py) or [src/models/external.py](src/models/external.py)
3. Implement handler logic in [src/handlers/](src/handlers/) (one file per tool)
4. Register tool in [src/server.py](src/server.py) using `@self.mcp.tool()` decorator
5. Add structured logging with `log_request()` and `log_response()`
6. Handle all exceptions with `handle_validation_error()`, `handle_api_error()`, or `handle_generic_error()`

## Important Notes

- **Logging**: Use structured logging via `get_logger(__name__)`. Never use `print()` for logs. The server outputs MCP protocol on stdout; logs go to stderr.
- **Type Safety**: All handlers use Pydantic models for validation. The codebase enforces strict typing with mypy (see [pyproject.toml](pyproject.toml) `[tool.mypy]`).
- **No Cross-Provider Coupling**: Handlers coordinate providers but API clients must not depend on each other.
- **Generated Artifacts**: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `htmlcov/` are gitignored and should never be committed.
