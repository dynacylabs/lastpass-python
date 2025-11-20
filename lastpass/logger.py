"""
Logging system with configurable levels and file output
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from enum import IntEnum
from typing import Optional


class LogLevel(IntEnum):
    """Log levels"""
    DEBUG = 0
    VERBOSE = 1
    INFO = 2
    WARNING = 3
    ERROR = 4


class Logger:
    """Structured logging system"""
    
    _instance: Optional['Logger'] = None
    _log_file: Optional[Path] = None
    _log_level: Optional[int] = None
    
    def __init__(self):
        self.config_dir = self._get_config_dir()
    
    @classmethod
    def get_instance(cls) -> 'Logger':
        """Get singleton logger instance"""
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    
    @staticmethod
    def _get_config_dir() -> Path:
        """Get configuration directory"""
        if "XDG_CONFIG_HOME" in os.environ:
            config_home = Path(os.environ["XDG_CONFIG_HOME"])
        else:
            config_home = Path.home() / ".config"
        return config_home / "lpass"
    
    def get_log_level(self) -> int:
        """Get configured log level"""
        if self._log_level is not None:
            return self._log_level
        
        level_str = os.environ.get('LPASS_LOG_LEVEL', '').upper()
        
        if level_str == 'DEBUG':
            self._log_level = LogLevel.DEBUG
        elif level_str == 'VERBOSE':
            self._log_level = LogLevel.VERBOSE
        elif level_str == 'INFO':
            self._log_level = LogLevel.INFO
        elif level_str == 'WARNING':
            self._log_level = LogLevel.WARNING
        elif level_str == 'ERROR':
            self._log_level = LogLevel.ERROR
        else:
            # Default: only errors
            self._log_level = LogLevel.ERROR
        
        return self._log_level
    
    def get_log_file(self) -> Optional[Path]:
        """Get log file path"""
        if self._log_file is not None:
            return self._log_file
        
        # Only create log file if logging is enabled
        if self.get_log_level() < LogLevel.ERROR:
            self._log_file = self.config_dir / "lpass.log"
            self.config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            return self._log_file
        
        return None
    
    def log(self, level: int, message: str, *args) -> None:
        """
        Log a message if level is enabled
        
        Args:
            level: Log level (LogLevel enum value)
            message: Message format string
            *args: Format arguments
        """
        if level < self.get_log_level():
            return
        
        # Format message
        if args:
            try:
                formatted_message = message % args
            except (TypeError, ValueError):
                formatted_message = message
        else:
            formatted_message = message
        
        # Add timestamp and level
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_name = LogLevel(level).name
        log_line = f"[{timestamp}] {level_name}: {formatted_message}\n"
        
        # Write to log file
        log_file = self.get_log_file()
        if log_file:
            try:
                with open(log_file, 'a') as f:
                    f.write(log_line)
            except Exception:
                pass
        
        # Also write to stderr for errors
        if level >= LogLevel.ERROR:
            sys.stderr.write(log_line)
    
    def debug(self, message: str, *args) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, *args)
    
    def verbose(self, message: str, *args) -> None:
        """Log verbose message"""
        self.log(LogLevel.VERBOSE, message, *args)
    
    def info(self, message: str, *args) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, message, *args)
    
    def warning(self, message: str, *args) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, message, *args)
    
    def error(self, message: str, *args) -> None:
        """Log error message"""
        self.log(LogLevel.ERROR, message, *args)


# Global logger instance
def get_logger() -> Logger:
    """Get global logger instance"""
    return Logger.get_instance()
