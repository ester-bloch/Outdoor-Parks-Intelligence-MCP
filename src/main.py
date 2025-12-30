#!/usr/bin/env python3
"""Main entry point for the Python MCP National Parks server."""

import argparse
import sys
from typing import NoReturn

from src.config import settings
from src.server import get_server
from src.utils.logging import configure_logging, get_logger


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        prog="python-mcp-nationalparks",
        description="National Parks MCP Server - Provides access to U.S. National Parks data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the server with default settings
  python-mcp-nationalparks

  # Start with debug logging
  python-mcp-nationalparks --log-level DEBUG

  # Start with JSON formatted logs
  python-mcp-nationalparks --log-json

  # Display version information
  python-mcp-nationalparks --version

Environment Variables:
  NPS_API_KEY          National Park Service API key (required)
  NPS_API_BASE_URL     Base URL for NPS API (default: https://developer.nps.gov/api/v1)
  LOG_LEVEL            Logging level (default: INFO)
  LOG_JSON             Output logs in JSON format (default: false)
  SERVER_NAME          Server name for MCP (default: National Parks)

Get your free NPS API key at:
  https://www.nps.gov/subjects/developer/get-started.htm
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
        help="Show version information and exit",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Set logging level (overrides LOG_LEVEL environment variable)",
    )

    parser.add_argument(
        "--log-json",
        action="store_true",
        default=None,
        help="Output logs in JSON format (overrides LOG_JSON environment variable)",
    )

    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        default=False,
        help="Disable timestamps in log output",
    )

    return parser.parse_args()


def main() -> NoReturn:
    """
    Start the National Parks MCP server.

    This function initializes the server, configures logging, validates
    the API key, and starts the FastMCP server with stdio transport.

    Exits:
        0: Normal shutdown
        1: Fatal error during startup or execution
    """
    # Parse command-line arguments
    args = parse_args()

    # Override settings with command-line arguments if provided
    if args.log_level is not None:
        settings.log_level = args.log_level

    if args.log_json is not None:
        settings.log_json = args.log_json

    if args.no_timestamp:
        settings.log_include_timestamp = False

    # Configure structured logging
    configure_logging(
        log_level=settings.log_level,
        json_logs=settings.log_json,
        include_timestamp=settings.log_include_timestamp,
    )

    logger = get_logger(__name__)

    # Validate API key configuration
    if not settings.nps_api_key:
        logger.warning(
            "api_key_not_configured",
            message="NPS_API_KEY not configured. Some functionality may be limited.",
        )
        print(
            "Warning: NPS_API_KEY is not set in environment variables.",
            file=sys.stderr,
        )
        print(
            "Get your API key at: https://www.nps.gov/subjects/developer/get-started.htm",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

    # Log server startup information
    logger.info(
        "server_starting",
        server_name=settings.server_name,
        api_base_url=settings.nps_api_base_url,
        log_level=settings.log_level,
        log_format="json" if settings.log_json else "console",
    )

    # Print startup message to stderr (stdout is used for MCP protocol)
    print(f"{settings.server_name} MCP Server running on stdio", file=sys.stderr)

    try:
        # Initialize and run FastMCP server
        server = get_server()
        server.run()
    except KeyboardInterrupt:
        logger.info("server_shutdown", reason="keyboard_interrupt")
        print("\nServer shutdown by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        logger.error("server_fatal_error", error=str(e), exc_info=True)
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
