"""
Pinentry integration for secure password prompts
"""

import os
import sys
import subprocess
import shutil
from typing import Optional
import getpass


class Pinentry:
    """Pinentry integration for GUI password prompts"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if pinentry is available"""
        if os.environ.get('LPASS_DISABLE_PINENTRY') == '1':
            return False
        
        pinentry_path = Pinentry._get_pinentry_path()
        return pinentry_path is not None
    
    @staticmethod
    def _get_pinentry_path() -> Optional[str]:
        """Get pinentry executable path"""
        # Check environment variable
        custom_path = os.environ.get('LPASS_PINENTRY')
        if custom_path and shutil.which(custom_path):
            return custom_path
        
        # Try common pinentry variants
        variants = [
            'pinentry',
            'pinentry-qt',
            'pinentry-gtk-2',
            'pinentry-gnome3',
            'pinentry-curses',
            'pinentry-tty'
        ]
        
        for variant in variants:
            path = shutil.which(variant)
            if path:
                return path
        
        return None
    
    @staticmethod
    def _escape(text: str) -> str:
        """Escape text for pinentry protocol"""
        result = []
        for char in text:
            if char == '%':
                result.append('%25')
            elif char == '\n':
                result.append('%0A')
            elif char == '\r':
                result.append('%0D')
            else:
                result.append(char)
        return ''.join(result)
    
    @staticmethod
    def _unescape(text: str) -> str:
        """Unescape text from pinentry protocol"""
        result = []
        i = 0
        while i < len(text):
            if text[i] == '%' and i + 2 < len(text):
                hex_str = text[i+1:i+3]
                try:
                    char_code = int(hex_str, 16)
                    result.append(chr(char_code))
                    i += 3
                    continue
                except ValueError:
                    pass
            result.append(text[i])
            i += 1
        return ''.join(result)
    
    @staticmethod
    def prompt_password(prompt: str, description: Optional[str] = None,
                       error: Optional[str] = None) -> Optional[str]:
        """
        Prompt for password using pinentry
        
        Args:
            prompt: Password prompt text
            description: Optional description
            error: Optional error message from previous attempt
        
        Returns:
            Password or None if cancelled
        """
        # Fall back to terminal if pinentry not available
        if not Pinentry.is_available():
            return Pinentry._terminal_prompt(prompt, description, error)
        
        pinentry_path = Pinentry._get_pinentry_path()
        if not pinentry_path:
            return Pinentry._terminal_prompt(prompt, description, error)
        
        try:
            # Start pinentry process
            proc = subprocess.Popen(
                [pinentry_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            commands = []
            
            # Set options
            if os.environ.get('TERM'):
                commands.append(f"OPTION ttytype={os.environ['TERM']}")
            
            if os.environ.get('DISPLAY'):
                commands.append(f"OPTION display={os.environ['DISPLAY']}")
            
            # Set prompts
            commands.append(f"SETPROMPT {Pinentry._escape(prompt)}")
            
            if description:
                commands.append(f"SETDESC {Pinentry._escape(description)}")
            
            if error:
                commands.append(f"SETERROR {Pinentry._escape(error)}")
            
            # Get password
            commands.append("GETPIN")
            
            # Send commands
            input_text = '\n'.join(commands) + '\n'
            stdout, stderr = proc.communicate(input=input_text, timeout=300)
            
            # Parse response
            for line in stdout.splitlines():
                if line.startswith('D '):
                    # Password data
                    password = Pinentry._unescape(line[2:])
                    return password
                elif line.startswith('ERR'):
                    # Cancelled or error
                    return None
            
            return None
        
        except Exception:
            # Fall back to terminal
            return Pinentry._terminal_prompt(prompt, description, error)
    
    @staticmethod
    def _terminal_prompt(prompt: str, description: Optional[str] = None,
                        error: Optional[str] = None) -> Optional[str]:
        """Fallback to terminal password prompt"""
        if error:
            print(f"Error: {error}", file=sys.stderr)
        
        if description:
            print(description)
        
        try:
            return getpass.getpass(f"{prompt}: ")
        except (KeyboardInterrupt, EOFError):
            return None


class AskpassPrompt:
    """Custom askpass program support"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if custom askpass is configured"""
        askpass = os.environ.get('LPASS_ASKPASS')
        return askpass is not None and shutil.which(askpass) is not None
    
    @staticmethod
    def prompt_password(prompt: str) -> Optional[str]:
        """
        Prompt for password using custom askpass program
        
        Args:
            prompt: Password prompt text
        
        Returns:
            Password or None if failed
        """
        askpass = os.environ.get('LPASS_ASKPASS')
        if not askpass:
            return None
        
        try:
            result = subprocess.run(
                [askpass, prompt],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None


def prompt_password(prompt: str = "Password",
                   description: Optional[str] = None,
                   error: Optional[str] = None) -> Optional[str]:
    """
    Prompt for password using best available method
    
    Args:
        prompt: Password prompt text
        description: Optional description
        error: Optional error message
    
    Returns:
        Password or None if cancelled
    """
    # Try custom askpass first
    if AskpassPrompt.is_available() and description:
        password = AskpassPrompt.prompt_password(description)
        if password:
            return password
    
    # Try pinentry
    if Pinentry.is_available():
        return Pinentry.prompt_password(prompt, description, error)
    
    # Fall back to terminal
    return Pinentry._terminal_prompt(prompt, description, error)
