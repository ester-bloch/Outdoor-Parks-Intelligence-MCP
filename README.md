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

### Available Tools

The server provides six tools for accessing National Parks data:

- `find_parks` - Search parks by state, activity, or keyword
- `get_park_details` - Get detailed information about a specific park
- `get_alerts` - Check current park alerts and closures
- `get_visitor_centers` - Find visitor centers and operating hours
- `get_campgrounds` - Discover campgrounds and amenities
- `get_events` - Find upcoming park events and programs

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
- Inspired by the original TypeScript implementation
