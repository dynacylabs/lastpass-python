"""Tests for logger module."""
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
import os
import sys
from pathlib import Path
from datetime import datetime

from lastpass.logger import Logger, LogLevel, get_logger


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary config directory."""
    config_dir = tmp_path / "lpass"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def logger(temp_config_dir, monkeypatch):
    """Create logger with temporary config."""
    # Reset singleton
    Logger._instance = None
    Logger._log_file = None
    Logger._log_level = None
    
    def mock_get_config_dir():
        return temp_config_dir
    
    monkeypatch.setattr(Logger, '_get_config_dir', staticmethod(mock_get_config_dir))
    return Logger()


@pytest.mark.unit
class TestLogLevel:
    """Tests for LogLevel enum."""
    
    def test_log_levels_order(self):
        """Test log levels are ordered correctly."""
        assert LogLevel.DEBUG < LogLevel.VERBOSE
        assert LogLevel.VERBOSE < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARNING
        assert LogLevel.WARNING < LogLevel.ERROR
    
    def test_log_level_values(self):
        """Test log level numeric values."""
        assert LogLevel.DEBUG == 0
        assert LogLevel.VERBOSE == 1
        assert LogLevel.INFO == 2
        assert LogLevel.WARNING == 3
        assert LogLevel.ERROR == 4


@pytest.mark.unit
class TestLoggerInit:
    """Tests for Logger initialization."""
    
    def test_logger_init(self, logger):
        """Test logger initialization."""
        assert logger.config_dir is not None
        assert isinstance(logger.config_dir, Path)
    
    def test_get_instance_singleton(self):
        """Test get_instance returns singleton."""
        Logger._instance = None
        logger1 = Logger.get_instance()
        logger2 = Logger.get_instance()
        assert logger1 is logger2


@pytest.mark.unit
class TestGetLogLevel:
    """Tests for get_log_level method."""
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_get_log_level_debug(self, logger):
        """Test DEBUG log level from environment."""
        level = logger.get_log_level()
        assert level == LogLevel.DEBUG
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'VERBOSE'})
    def test_get_log_level_verbose(self, logger):
        """Test VERBOSE log level from environment."""
        level = logger.get_log_level()
        assert level == LogLevel.VERBOSE
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'INFO'})
    def test_get_log_level_info(self, logger):
        """Test INFO log level from environment."""
        level = logger.get_log_level()
        assert level == LogLevel.INFO
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'WARNING'})
    def test_get_log_level_warning(self, logger):
        """Test WARNING log level from environment."""
        level = logger.get_log_level()
        assert level == LogLevel.WARNING
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'ERROR'})
    def test_get_log_level_error(self, logger):
        """Test ERROR log level from environment."""
        level = logger.get_log_level()
        assert level == LogLevel.ERROR
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_log_level_default(self, logger):
        """Test default log level (ERROR)."""
        level = logger.get_log_level()
        assert level == LogLevel.ERROR
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'invalid'})
    def test_get_log_level_invalid(self, logger):
        """Test invalid log level defaults to ERROR."""
        level = logger.get_log_level()
        assert level == LogLevel.ERROR
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'debug'})
    def test_get_log_level_lowercase(self, logger):
        """Test lowercase log level."""
        level = logger.get_log_level()
        assert level == LogLevel.DEBUG
    
    def test_get_log_level_cached(self, logger):
        """Test log level is cached."""
        with patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'}):
            level1 = logger.get_log_level()
        
        # Change environment, should still return cached value
        with patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'ERROR'}):
            level2 = logger.get_log_level()
        
        assert level1 == level2 == LogLevel.DEBUG


@pytest.mark.unit
class TestGetLogFile:
    """Tests for get_log_file method."""
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_get_log_file_debug(self, logger, temp_config_dir):
        """Test log file created for DEBUG level."""
        log_file = logger.get_log_file()
        assert log_file is not None
        assert log_file == temp_config_dir / "lpass.log"
        assert temp_config_dir.exists()
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'ERROR'})
    def test_get_log_file_error_none(self, logger):
        """Test no log file for ERROR level (default)."""
        log_file = logger.get_log_file()
        assert log_file is None
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'INFO'})
    def test_get_log_file_cached(self, logger, temp_config_dir):
        """Test log file path is cached."""
        log_file1 = logger.get_log_file()
        log_file2 = logger.get_log_file()
        assert log_file1 is log_file2


@pytest.mark.unit
class TestLog:
    """Tests for log method."""
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_log_to_file(self, logger, temp_config_dir):
        """Test logging to file."""
        log_file = temp_config_dir / "lpass.log"
        logger.log(LogLevel.DEBUG, "Test message")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "DEBUG: Test message" in content
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'INFO'})
    def test_log_filtered_by_level(self, logger, temp_config_dir):
        """Test messages filtered by log level."""
        log_file = temp_config_dir / "lpass.log"
        logger.log(LogLevel.DEBUG, "Debug message")
        logger.log(LogLevel.INFO, "Info message")
        
        content = log_file.read_text()
        assert "Debug message" not in content
        assert "Info message" in content
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_log_with_format_args(self, logger, temp_config_dir):
        """Test logging with format arguments."""
        log_file = temp_config_dir / "lpass.log"
        logger.log(LogLevel.DEBUG, "User: %s, Count: %d", "test", 42)
        
        content = log_file.read_text()
        assert "User: test, Count: 42" in content
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_log_format_error_handled(self, logger, temp_config_dir):
        """Test format errors are handled gracefully."""
        log_file = temp_config_dir / "lpass.log"
        logger.log(LogLevel.DEBUG, "Message with %s", "too", "many", "args")
        
        # Should log something even if format fails
        assert log_file.exists()
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_log_includes_timestamp(self, logger, temp_config_dir):
        """Test log includes timestamp."""
        log_file = temp_config_dir / "lpass.log"
        logger.log(LogLevel.DEBUG, "Test message")
        
        content = log_file.read_text()
        # Should contain date in format YYYY-MM-DD
        assert datetime.now().strftime("%Y-%m-%d") in content
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_log_includes_level_name(self, logger, temp_config_dir):
        """Test log includes level name."""
        log_file = temp_config_dir / "lpass.log"
        logger.log(LogLevel.DEBUG, "Test")
        logger.log(LogLevel.INFO, "Test")
        logger.log(LogLevel.ERROR, "Test")
        
        content = log_file.read_text()
        assert "DEBUG:" in content
        assert "INFO:" in content
        assert "ERROR:" in content
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'ERROR'})
    def test_log_error_to_stderr(self, logger):
        """Test errors also go to stderr."""
        with patch('sys.stderr.write') as mock_stderr:
            logger.log(LogLevel.ERROR, "Error message")
            mock_stderr.assert_called()
            call_args = str(mock_stderr.call_args)
            assert "Error message" in call_args
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_log_file_write_error_handled(self, logger, temp_config_dir):
        """Test file write errors are handled."""
        log_file = temp_config_dir / "lpass.log"
        
        # Make directory read-only
        with patch('builtins.open', side_effect=PermissionError()):
            # Should not raise exception
            logger.log(LogLevel.DEBUG, "Test message")


@pytest.mark.unit
class TestLoggerConvenienceMethods:
    """Tests for convenience logging methods."""
    
    @patch.object(Logger, 'log')
    def test_debug(self, mock_log, logger):
        """Test debug() method."""
        logger.debug("Debug message")
        mock_log.assert_called_once_with(LogLevel.DEBUG, "Debug message")
    
    @patch.object(Logger, 'log')
    def test_verbose(self, mock_log, logger):
        """Test verbose() method."""
        logger.verbose("Verbose message")
        mock_log.assert_called_once_with(LogLevel.VERBOSE, "Verbose message")
    
    @patch.object(Logger, 'log')
    def test_info(self, mock_log, logger):
        """Test info() method."""
        logger.info("Info message")
        mock_log.assert_called_once_with(LogLevel.INFO, "Info message")
    
    @patch.object(Logger, 'log')
    def test_warning(self, mock_log, logger):
        """Test warning() method."""
        logger.warning("Warning message")
        mock_log.assert_called_once_with(LogLevel.WARNING, "Warning message")
    
    @patch.object(Logger, 'log')
    def test_error(self, mock_log, logger):
        """Test error() method."""
        logger.error("Error message")
        mock_log.assert_called_once_with(LogLevel.ERROR, "Error message")
    
    @patch.object(Logger, 'log')
    def test_convenience_methods_with_args(self, mock_log, logger):
        """Test convenience methods with format args."""
        logger.debug("User: %s", "test")
        mock_log.assert_called_with(LogLevel.DEBUG, "User: %s", "test")


@pytest.mark.unit
class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_returns_instance(self):
        """Test get_logger returns logger instance."""
        Logger._instance = None
        logger = get_logger()
        assert isinstance(logger, Logger)
    
    def test_get_logger_singleton(self):
        """Test get_logger returns same instance."""
        Logger._instance = None
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2


@pytest.mark.unit
class TestLoggerIntegration:
    """Integration tests for logger."""
    
    @patch.dict(os.environ, {'LPASS_LOG_LEVEL': 'DEBUG'})
    def test_multiple_log_calls(self, logger, temp_config_dir):
        """Test multiple log calls append to file."""
        log_file = temp_config_dir / "lpass.log"
        
        logger.debug("Message 1")
        logger.info("Message 2")
        logger.error("Message 3")
        
        content = log_file.read_text()
        assert "Message 1" in content
        assert "Message 2" in content
        assert "Message 3" in content
        
        # Should have 3 lines
        lines = [l for l in content.splitlines() if l.strip()]
        assert len(lines) >= 3
