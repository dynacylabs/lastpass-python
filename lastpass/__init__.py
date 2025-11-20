"""
LastPass Python CLI and API Library

A complete Python implementation of the LastPass CLI with a friendly API interface.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"

from .client import LastPassClient
from .models import Account, Field, Share, Attachment, ShareUser, ShareLimit
from .exceptions import (
    LastPassException,
    LoginFailedException,
    InvalidSessionException,
    NetworkException,
    DecryptionException,
)
from .note_types import NoteType, get_note_type_by_shortname, get_note_type_by_name
from .clipboard import ClipboardManager
from .terminal import Terminal, ColorMode
from .config import Config
from .agent import Agent
from .upload_queue import UploadQueue
from .feature_flag import FeatureFlag
from .logger import Logger, LogLevel, get_logger
from .pinentry import Pinentry, AskpassPrompt, prompt_password
from .editor import Editor
from .process_security import ProcessSecurity, SecureString, SecureBytes
from .notes import notes_expand, notes_collapse, is_secure_note
from .browser import open_url, get_browser_command

__all__ = [
    "LastPassClient",
    "Account",
    "Field",
    "Share",
    "ShareUser",
    "ShareLimit",
    "Attachment",
    "LastPassException",
    "LoginFailedException",
    "InvalidSessionException",
    "NetworkException",
    "DecryptionException",
    "NoteType",
    "get_note_type_by_shortname",
    "get_note_type_by_name",
    "ClipboardManager",
    "Terminal",
    "ColorMode",
    "Config",
    "Agent",
    "UploadQueue",
    "FeatureFlag",
    "Logger",
    "LogLevel",
    "get_logger",
    "Pinentry",
    "AskpassPrompt",
    "prompt_password",
    "Editor",
    "ProcessSecurity",
    "SecureString",
    "SecureBytes",
    "notes_expand",
    "notes_collapse",
    "is_secure_note",
    "open_url",
    "get_browser_command",
]
