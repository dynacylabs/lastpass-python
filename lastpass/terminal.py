"""
Terminal output formatting with color support
"""

import os
import sys
from enum import Enum
from typing import Optional


class ColorMode(Enum):
    """Color output modes"""
    AUTO = "auto"
    ALWAYS = "always"
    NEVER = "never"


class TerminalColors:
    """ANSI color codes"""
    # Foreground colors
    FG_BLACK = "\033[30m"
    FG_RED = "\033[31m"
    FG_GREEN = "\033[32m"
    FG_YELLOW = "\033[33m"
    FG_BLUE = "\033[34m"
    FG_MAGENTA = "\033[35m"
    FG_CYAN = "\033[36m"
    FG_WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    
    # Text attributes
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    
    # Reset
    RESET = "\033[0m"
    NO_BOLD = "\033[22m"
    NO_UNDERLINE = "\033[24m"


class Terminal:
    """Terminal output manager with color support"""
    
    _color_mode: ColorMode = ColorMode.AUTO
    _color_enabled: Optional[bool] = None
    
    @classmethod
    def set_color_mode(cls, mode: ColorMode) -> None:
        """Set color output mode"""
        cls._color_mode = mode
        cls._color_enabled = None  # Reset cached value
    
    @classmethod
    def parse_color_mode(cls, mode_str: str) -> ColorMode:
        """Parse color mode string"""
        mode_str = mode_str.lower()
        if mode_str == "always":
            return ColorMode.ALWAYS
        elif mode_str == "never":
            return ColorMode.NEVER
        else:
            return ColorMode.AUTO
    
    @classmethod
    def is_color_enabled(cls) -> bool:
        """Check if color output is enabled"""
        if cls._color_enabled is not None:
            return cls._color_enabled
        
        if cls._color_mode == ColorMode.ALWAYS:
            cls._color_enabled = True
        elif cls._color_mode == ColorMode.NEVER:
            cls._color_enabled = False
        else:  # AUTO
            # Check if stdout is a TTY
            cls._color_enabled = sys.stdout.isatty()
            
            # Also check NO_COLOR environment variable
            if os.environ.get('NO_COLOR'):
                cls._color_enabled = False
            
            # Check TERM environment variable
            term = os.environ.get('TERM', '')
            if term == 'dumb' or not term:
                cls._color_enabled = False
        
        return cls._color_enabled
    
    @classmethod
    def colorize(cls, text: str, *codes: str) -> str:
        """Apply color codes to text"""
        if not cls.is_color_enabled():
            return text
        
        prefix = ''.join(codes)
        return f"{prefix}{text}{TerminalColors.RESET}"
    
    @classmethod
    def print_colored(cls, text: str, *codes: str, **kwargs) -> None:
        """Print colored text"""
        print(cls.colorize(text, *codes), **kwargs)
    
    @classmethod
    def success(cls, text: str) -> str:
        """Format success message"""
        return cls.colorize(text, TerminalColors.FG_GREEN, TerminalColors.BOLD)
    
    @classmethod
    def error(cls, text: str) -> str:
        """Format error message"""
        return cls.colorize(text, TerminalColors.FG_RED, TerminalColors.BOLD)
    
    @classmethod
    def warning(cls, text: str) -> str:
        """Format warning message"""
        return cls.colorize(text, TerminalColors.FG_YELLOW, TerminalColors.BOLD)
    
    @classmethod
    def info(cls, text: str) -> str:
        """Format info message"""
        return cls.colorize(text, TerminalColors.FG_CYAN)
    
    @classmethod
    def bold(cls, text: str) -> str:
        """Format bold text"""
        return cls.colorize(text, TerminalColors.BOLD)
    
    @classmethod
    def underline(cls, text: str) -> str:
        """Format underlined text"""
        return cls.colorize(text, TerminalColors.UNDERLINE)
    
    @classmethod
    def header(cls, text: str) -> str:
        """Format header text"""
        return cls.colorize(text, TerminalColors.FG_YELLOW, TerminalColors.BOLD)
