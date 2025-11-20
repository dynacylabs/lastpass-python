"""
Clipboard integration for LastPass CLI
"""

import os
import subprocess
import sys
import time
from typing import Optional


class ClipboardManager:
    """Manage clipboard operations with support for custom commands"""
    
    @staticmethod
    def copy_to_clipboard(text: str, clear_after: Optional[int] = None) -> bool:
        """
        Copy text to clipboard
        
        Args:
            text: Text to copy
            clear_after: Seconds after which to clear clipboard (None = don't clear)
        
        Returns:
            True if successful, False otherwise
        """
        # Check for custom clipboard command
        custom_command = os.environ.get('LPASS_CLIPBOARD_COMMAND')
        
        if custom_command:
            return ClipboardManager._use_custom_command(custom_command, text)
        
        # Auto-detect clipboard tool
        return ClipboardManager._auto_clipboard(text, clear_after)
    
    @staticmethod
    def _use_custom_command(command: str, text: str) -> bool:
        """Use custom clipboard command"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            process.communicate(input=text.encode('utf-8'))
            return process.returncode == 0
        except Exception:
            return False
    
    @staticmethod
    def _auto_clipboard(text: str, clear_after: Optional[int] = None) -> bool:
        """Auto-detect and use appropriate clipboard tool"""
        # Try different clipboard tools in order of preference
        
        # Linux with X11
        if ClipboardManager._try_command(['xclip', '-selection', 'clipboard'], text):
            if clear_after:
                ClipboardManager._schedule_clear(clear_after)
            return True
        
        if ClipboardManager._try_command(['xsel', '--clipboard', '--input'], text):
            if clear_after:
                ClipboardManager._schedule_clear(clear_after)
            return True
        
        # Linux with Wayland
        if ClipboardManager._try_command(['wl-copy'], text):
            if clear_after:
                ClipboardManager._schedule_clear_wayland(clear_after)
            return True
        
        # macOS
        if ClipboardManager._try_command(['pbcopy'], text):
            if clear_after:
                ClipboardManager._schedule_clear_macos(clear_after)
            return True
        
        # Windows (WSL or native)
        if ClipboardManager._try_command(['clip.exe'], text):
            # No auto-clear on Windows
            return True
        
        # Termux (Android)
        if ClipboardManager._try_command(['termux-clipboard-set'], text):
            return True
        
        # Try Python's pyperclip as fallback
        try:
            import pyperclip
            pyperclip.copy(text)
            if clear_after:
                ClipboardManager._schedule_clear_generic(clear_after)
            return True
        except ImportError:
            pass
        
        return False
    
    @staticmethod
    def _try_command(command: list, text: str) -> bool:
        """Try to execute clipboard command"""
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            process.communicate(input=text.encode('utf-8'), timeout=5)
            return process.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return False
    
    @staticmethod
    def _schedule_clear(seconds: int) -> None:
        """Schedule clipboard clear for X11"""
        # Fork a background process to clear clipboard after delay
        try:
            if os.fork() == 0:
                # Child process
                time.sleep(seconds)
                subprocess.run(
                    ['xclip', '-selection', 'clipboard'],
                    input=b'',
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                sys.exit(0)
        except Exception:
            pass
    
    @staticmethod
    def _schedule_clear_wayland(seconds: int) -> None:
        """Schedule clipboard clear for Wayland"""
        try:
            if os.fork() == 0:
                time.sleep(seconds)
                subprocess.run(
                    ['wl-copy', '--clear'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                sys.exit(0)
        except Exception:
            pass
    
    @staticmethod
    def _schedule_clear_macos(seconds: int) -> None:
        """Schedule clipboard clear for macOS"""
        try:
            if os.fork() == 0:
                time.sleep(seconds)
                subprocess.run(
                    ['pbcopy'],
                    input=b'',
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                sys.exit(0)
        except Exception:
            pass
    
    @staticmethod
    def _schedule_clear_generic(seconds: int) -> None:
        """Schedule clipboard clear using pyperclip"""
        try:
            if os.fork() == 0:
                time.sleep(seconds)
                try:
                    import pyperclip
                    pyperclip.copy('')
                except ImportError:
                    pass
                sys.exit(0)
        except Exception:
            pass
    
    @staticmethod
    def get_clipboard_timeout() -> Optional[int]:
        """Get clipboard clear timeout from environment"""
        timeout_str = os.environ.get('LPASS_CLIP_CLEAR_TIME', '45')
        try:
            timeout = int(timeout_str)
            return timeout if timeout > 0 else None
        except ValueError:
            return 45  # Default to 45 seconds
