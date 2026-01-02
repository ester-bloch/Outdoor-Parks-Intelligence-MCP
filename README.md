# Python MCP National Parks Server

A Python implementation of the Model Context Protocol (MCP) server for accessing U.S. National Parks data through the National Park Service API.

## Features

- **FastMCP Integration**: Built using the official Python MCP SDK
- **Type Safety**: Full Pydantic validation and type hints
- **Modern HTTP Client**: HTTPX for reliable API communication
- **Comprehensive Testing**: Unit tests and property-based testing
- **Development Tools**: Black, flake8, mypy, and pre-commit hooks

## Installation

### Prerequisites

- Python 3.8 or higher
- Poetry (recommended) or pip

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd python-mcp-nationalparks

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
# Clone the repository
git clone <repository-url>
cd python-mcp-nationalparks

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

1. Get a free API key from the [National Park Service](https://www.nps.gov/subjects/developer/get-started.htm)

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your API key:
   ```
   NPS_API_KEY=your_nps_api_key_here
   ```

## Usage

### Running the Server

```bash
# Using Poetry
poetry run python-mcp-nationalparks

# Using pip installation
python-mcp-nationalparks
```

### Quick Demo (2 minutes)

1) Install dependencies

```bash
# Option A: Poetry
poetry install

# Option B: pip (editable)
pip install -e .
```

2) (Recommended) Configure your NPS API key

```bash
cp .env.example .env
# then edit .env and set NPS_API_KEY=...
```

3) Run the server (stdio)

```bash
# If installed via Poetry
poetry run python-mcp-nationalparks

# Or directly (works from repo root)
python -m src.main
```

4) Run the fallback demo client (spawns the server and calls a tool)

```bash
python scripts/demo.py
```

### Claude Desktop configuration

Use `docs/claude_desktop_config.json` as a template. Replace `YOUR_NPS_API_KEY_HERE` with your real key and add it to your Claude Desktop configuration.

### Available Tools

The server provides six tools for accessing National Parks data:

- `findParks` - Search parks by state, activity, or keyword
- `getParkDetails` - Get detailed information about a specific park
- `getAlerts` - Check current park alerts and closures
- `getVisitorCenters` - Find visitor centers and operating hours
- `getCampgrounds` - Discover campgrounds and amenities
- `getEvents` - Find upcoming park events and programs
- `getAirQuality` - Get air quality (AirVisual) by park code or coordinates
- `getWeather` - Get current weather (OpenWeather or Open-Meteo fallback)
- `getParkContext` - Combined NPS + weather + air quality snapshot

## Development

### Setup Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test types
poetry run pytest tests/unit/
poetry run pytest tests/integration/
poetry run pytest tests/property/
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Sort imports
poetry run isort src tests

# Lint code
poetry run flake8 src tests

# Type checking
poetry run mypy src
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run mypy
```

## Project Structure

```
src/
├── __init__.py
├── main.py                 # Entry point
├── server.py              # FastMCP server setup
├── config.py              # Configuration management
├── models/                # Pydantic data models
│   ├── __init__.py
│   ├── requests.py        # Tool input models
│   ├── responses.py       # API response models
│   └── errors.py          # Error models
├── handlers/              # Tool implementations
│   ├── __init__.py
│   ├── find_parks.py
│   ├── get_park_details.py
│   ├── get_alerts.py
│   ├── get_visitor_centers.py
│   ├── get_campgrounds.py
│   └── get_events.py
├── api/                   # NPS API client
│   ├── __init__.py
│   ├── client.py          # HTTPX client
│   ├── auth.py            # Authentication
│   └── rate_limit.py      # Rate limiting
└── utils/                 # Utility functions
    ├── __init__.py
    ├── logging.py         # Logging setup
    └── formatters.py      # Data formatters

tests/
├── unit/                  # Unit tests
├── integration/           # Integration tests
├── property/              # Property-based tests
└── conftest.py           # Pytest configuration
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure code quality
5. Submit a pull request


## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Data provided by the [National Park Service API](https://www.nps.gov/subjects/developer/)
