"""Unit tests for main entry point."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.main import main, parse_args


class TestParseArgs:
    """Tests for command-line argument parsing."""

    def test_parse_args_default(self):
        """Test parsing with no arguments."""
        with patch.object(sys, "argv", ["python-mcp-nationalparks"]):
            args = parse_args()
            assert args.log_level is None
            assert args.log_json is None
            assert args.no_timestamp is False

    def test_parse_args_log_level(self):
        """Test parsing with log level argument."""
        with patch.object(
            sys, "argv", ["python-mcp-nationalparks", "--log-level", "DEBUG"]
        ):
            args = parse_args()
            assert args.log_level == "DEBUG"

    def test_parse_args_log_json(self):
        """Test parsing with log-json flag."""
        with patch.object(sys, "argv", ["python-mcp-nationalparks", "--log-json"]):
            args = parse_args()
            assert args.log_json is True

    def test_parse_args_no_timestamp(self):
        """Test parsing with no-timestamp flag."""
        with patch.object(sys, "argv", ["python-mcp-nationalparks", "--no-timestamp"]):
            args = parse_args()
            assert args.no_timestamp is True

    def test_parse_args_combined(self):
        """Test parsing with multiple arguments."""
        with patch.object(
            sys,
            "argv",
            [
                "python-mcp-nationalparks",
                "--log-level",
                "ERROR",
                "--log-json",
                "--no-timestamp",
            ],
        ):
            args = parse_args()
            assert args.log_level == "ERROR"
            assert args.log_json is True
            assert args.no_timestamp is True

    def test_parse_args_invalid_log_level(self):
        """Test parsing with invalid log level."""
        with patch.object(
            sys, "argv", ["python-mcp-nationalparks", "--log-level", "INVALID"]
        ):
            with pytest.raises(SystemExit):
                parse_args()


class TestMain:
    """Tests for main function."""

    @patch("src.main.get_server")
    @patch("src.main.configure_logging")
    @patch("src.main.get_logger")
    @patch.object(sys, "argv", ["python-mcp-nationalparks"])
    def test_main_starts_server(
        self, mock_get_logger, mock_configure_logging, mock_get_server
    ):
        """Test that main function starts the server."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_server = MagicMock()
        mock_get_server.return_value = mock_server

        # Run main and expect it to call server.run()
        with pytest.raises(SystemExit) as exc_info:
            # Mock server.run() to raise SystemExit to prevent infinite loop
            mock_server.run.side_effect = SystemExit(0)
            main()

        # Verify server was started
        assert exc_info.value.code == 0
        mock_get_server.assert_called_once()
        mock_server.run.assert_called_once()

    @patch("src.main.get_server")
    @patch("src.main.configure_logging")
    @patch("src.main.get_logger")
    @patch.object(sys, "argv", ["python-mcp-nationalparks", "--log-level", "DEBUG"])
    def test_main_with_cli_args(
        self, mock_get_logger, mock_configure_logging, mock_get_server
    ):
        """Test that main function respects CLI arguments."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_server = MagicMock()
        mock_get_server.return_value = mock_server
        mock_server.run.side_effect = SystemExit(0)

        # Run main
        with pytest.raises(SystemExit):
            main()

        # Verify logging was configured with DEBUG level
        mock_configure_logging.assert_called_once()
        call_kwargs = mock_configure_logging.call_args[1]
        assert call_kwargs["log_level"] == "DEBUG"

    @patch("src.main.get_server")
    @patch("src.main.configure_logging")
    @patch("src.main.get_logger")
    @patch.object(sys, "argv", ["python-mcp-nationalparks"])
    def test_main_handles_keyboard_interrupt(
        self, mock_get_logger, mock_configure_logging, mock_get_server
    ):
        """Test that main function handles KeyboardInterrupt gracefully."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_server = MagicMock()
        mock_get_server.return_value = mock_server
        mock_server.run.side_effect = KeyboardInterrupt()

        # Run main and expect clean exit
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        mock_logger.info.assert_called()

    @patch("src.main.get_server")
    @patch("src.main.configure_logging")
    @patch("src.main.get_logger")
    @patch.object(sys, "argv", ["python-mcp-nationalparks"])
    def test_main_handles_exception(
        self, mock_get_logger, mock_configure_logging, mock_get_server
    ):
        """Test that main function handles exceptions and exits with error code."""
        # Setup mocks
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_server = MagicMock()
        mock_get_server.return_value = mock_server
        mock_server.run.side_effect = RuntimeError("Test error")

        # Run main and expect error exit
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_logger.error.assert_called()
