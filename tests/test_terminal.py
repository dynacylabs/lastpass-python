"""
Tests for terminal color functionality
"""

import pytest
from unittest.mock import patch

from lastpass.terminal import Terminal, ColorMode, TerminalColors


class TestTerminal:
    """Test terminal color functionality"""
    
    def test_color_mode_always(self):
        """Test always color mode"""
        Terminal.set_color_mode(ColorMode.ALWAYS)
        assert Terminal.is_color_enabled() is True
    
    def test_color_mode_never(self):
        """Test never color mode"""
        Terminal.set_color_mode(ColorMode.NEVER)
        assert Terminal.is_color_enabled() is False
    
    def test_color_mode_auto_tty(self):
        """Test auto color mode with TTY"""
        Terminal.set_color_mode(ColorMode.AUTO)
        Terminal._color_enabled = None  # Reset cache
        
        with patch('sys.stdout.isatty', return_value=True):
            assert Terminal.is_color_enabled() is True
    
    def test_color_mode_auto_no_tty(self):
        """Test auto color mode without TTY"""
        Terminal.set_color_mode(ColorMode.AUTO)
        Terminal._color_enabled = None  # Reset cache
        
        with patch('sys.stdout.isatty', return_value=False):
            assert Terminal.is_color_enabled() is False
    
    def test_colorize_enabled(self):
        """Test colorize with colors enabled"""
        Terminal.set_color_mode(ColorMode.ALWAYS)
        result = Terminal.colorize("test", TerminalColors.FG_GREEN)
        assert result == f"{TerminalColors.FG_GREEN}test{TerminalColors.RESET}"
    
    def test_colorize_disabled(self):
        """Test colorize with colors disabled"""
        Terminal.set_color_mode(ColorMode.NEVER)
        result = Terminal.colorize("test", TerminalColors.FG_GREEN)
        assert result == "test"
    
    def test_success_message(self):
        """Test success message formatting"""
        Terminal.set_color_mode(ColorMode.ALWAYS)
        result = Terminal.success("Success")
        assert TerminalColors.FG_GREEN in result
        assert TerminalColors.BOLD in result
    
    def test_error_message(self):
        """Test error message formatting"""
        Terminal.set_color_mode(ColorMode.ALWAYS)
        result = Terminal.error("Error")
        assert TerminalColors.FG_RED in result
    
    def test_parse_color_mode(self):
        """Test color mode parsing"""
        assert Terminal.parse_color_mode("always") == ColorMode.ALWAYS
        assert Terminal.parse_color_mode("never") == ColorMode.NEVER
        assert Terminal.parse_color_mode("auto") == ColorMode.AUTO
        assert Terminal.parse_color_mode("AUTO") == ColorMode.AUTO


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
