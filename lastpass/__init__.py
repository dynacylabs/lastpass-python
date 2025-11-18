"""
LastPass Python CLI and API Library

A complete Python implementation of the LastPass CLI with a friendly API interface.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"

from .client import LastPassClient
from .models import Account, Field, Share, Attachment
from .exceptions import (
    LastPassException,
    LoginFailedException,
    InvalidSessionException,
    NetworkException,
    DecryptionException,
)

__all__ = [
    "LastPassClient",
    "Account",
    "Field",
    "Share",
    "Attachment",
    "LastPassException",
    "LoginFailedException",
    "InvalidSessionException",
    "NetworkException",
    "DecryptionException",
]
