"""
Browser utilities for opening URLs
"""

import os
import subprocess
import webbrowser
from typing import Optional


def open_url(url: str) -> bool:
    """
    Open URL in browser
    
    Respects $BROWSER environment variable, falling back to system default.
    
    Args:
        url: URL to open
    
    Returns:
        True if successful, False otherwise
    """
    # Check for BROWSER environment variable (as in C implementation)
    browser_cmd = os.environ.get('BROWSER')
    
    if browser_cmd:
        try:
            # Replace $BROWSER <url> pattern
            cmd = browser_cmd.replace('%s', url) if '%s' in browser_cmd else f"{browser_cmd} {url}"
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            # Fall through to default
            pass
    
    # Use system default browser
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


def get_browser_command() -> Optional[str]:
    """
    Get the browser command that would be used
    
    Returns:
        Browser command or None if using system default
    """
    return os.environ.get('BROWSER')
