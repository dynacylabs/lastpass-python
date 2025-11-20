"""
Configuration management for LastPass CLI
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Configuration file manager"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = self._get_config_dir()
        self.config_dir = config_dir
        self.config_file = config_dir / "config.json"
        self._config: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def _get_config_dir() -> Path:
        """Get LastPass configuration directory"""
        # Check LPASS_HOME first (overrides everything)
        lpass_home = os.environ.get("LPASS_HOME")
        if lpass_home:
            return Path(lpass_home)
        
        # Use XDG_CONFIG_HOME or default
        if "XDG_CONFIG_HOME" in os.environ:
            config_home = Path(os.environ["XDG_CONFIG_HOME"])
        else:
            config_home = Path.home() / ".config"
        return config_home / "lpass"
    
    def _load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self._config is not None:
            return self._config
        
        if not self.config_file.exists():
            self._config = {}
            return self._config
        
        try:
            with open(self.config_file, 'r') as f:
                self._config = json.load(f)
        except Exception:
            self._config = {}
        
        return self._config
    
    def _save(self) -> None:
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        with open(self.config_file, 'w') as f:
            json.dump(self._config or {}, f, indent=2)
        
        os.chmod(self.config_file, 0o600)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        config = self._load()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        config = self._load()
        config[key] = value
        self._save()
    
    def delete(self, key: str) -> None:
        """Delete configuration value"""
        config = self._load()
        if key in config:
            del config[key]
            self._save()
    
    def get_alias(self, alias: str) -> Optional[str]:
        """Get command alias"""
        return self.get(f"alias.{alias}")
    
    def set_alias(self, alias: str, command: str) -> None:
        """Set command alias"""
        self.set(f"alias.{alias}", command)
    
    def delete_alias(self, alias: str) -> None:
        """Delete command alias"""
        self.delete(f"alias.{alias}")
    
    def expand_alias(self, args: list) -> list:
        """
        Expand alias in command arguments
        
        Aliases can be stored in two ways:
        1. In config.json as 'alias.{command}'
        2. In separate files as 'alias.{command}' in config directory
        """
        if not args:
            return args
        
        command = args[0]
        
        # First try to load from alias file
        alias_file = self.config_dir / f"alias.{command}"
        if alias_file.exists():
            try:
                with open(alias_file, 'r') as f:
                    alias_value = f.read().strip()
                    if alias_value:
                        # Split alias value and prepend to remaining args
                        expanded = alias_value.split()
                        return expanded + args[1:]
            except Exception:
                pass  # Fall through to check config
        
        # Then try config.json
        alias_value = self.get_alias(command)
        if alias_value:
            # Split alias value and prepend to remaining args
            expanded = alias_value.split()
            return expanded + args[1:]
        
        return args
    
    def write_buffer(self, key: str, data: bytes) -> None:
        """Write binary buffer to config file"""
        file_path = self.config_dir / key
        self.config_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        with open(file_path, 'wb') as f:
            f.write(data)
        
        os.chmod(file_path, 0o600)
    
    def read_buffer(self, key: str) -> Optional[bytes]:
        """Read binary buffer from config file"""
        file_path = self.config_dir / key
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception:
            return None
    
    def unlink(self, key: str) -> None:
        """Delete config file"""
        file_path = self.config_dir / key
        if file_path.exists():
            file_path.unlink()
    
    def has_plaintext_key(self) -> bool:
        """Check if plaintext key is stored"""
        return (self.config_dir / "plaintext_key").exists()
    
    def get_plaintext_key(self) -> Optional[bytes]:
        """Get stored plaintext key"""
        return self.read_buffer("plaintext_key")
    
    def set_plaintext_key(self, key: bytes) -> None:
        """Store plaintext key (WARNING: less secure)"""
        self.write_buffer("plaintext_key", key)
    
    def delete_plaintext_key(self) -> None:
        """Delete stored plaintext key"""
        self.unlink("plaintext_key")
    
    @staticmethod
    def get_auto_sync_time() -> int:
        """Get auto-sync time in seconds (0 = disabled)"""
        sync_time = os.environ.get("LPASS_AUTO_SYNC_TIME", "0")
        try:
            return int(sync_time)
        except ValueError:
            return 0
    
    @staticmethod
    def get_clipboard_command() -> Optional[str]:
        """Get custom clipboard command"""
        return os.environ.get("LPASS_CLIPBOARD_COMMAND")
    
    @staticmethod
    def is_agent_disabled() -> bool:
        """Check if agent is disabled"""
        return os.environ.get("LPASS_AGENT_DISABLE") == "1"
    
    @staticmethod
    def get_agent_timeout() -> int:
        """Get agent timeout in seconds (0 = never expire)"""
        timeout = os.environ.get("LPASS_AGENT_TIMEOUT", "3600")
        try:
            return int(timeout)
        except ValueError:
            return 3600
    
    @staticmethod
    def get_log_level() -> str:
        """Get log level"""
        return os.environ.get("LPASS_LOG_LEVEL", "ERROR").upper()
    
    @staticmethod
    def get_askpass() -> Optional[str]:
        """Get custom askpass program"""
        return os.environ.get("LPASS_ASKPASS")
    
    @staticmethod
    def get_pinentry() -> Optional[str]:
        """Get custom pinentry program"""
        return os.environ.get("LPASS_PINENTRY")
    
    @staticmethod
    def is_pinentry_disabled() -> bool:
        """Check if pinentry is disabled"""
        return os.environ.get("LPASS_DISABLE_PINENTRY") == "1"
    
    @staticmethod
    def get_secure_tmpdir() -> Optional[str]:
        """Get secure temporary directory"""
        return os.environ.get("SECURE_TMPDIR")

