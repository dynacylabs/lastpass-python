"""
Main LastPass client with friendly Python API
"""

import os
import re
import secrets
import string
from pathlib import Path
from typing import List, Optional, Dict, Any
from getpass import getpass

from .session import Session
from .http import HTTPClient
from .kdf import derive_keys
from .blob import parse_blob
from .xml_parser import parse_login_response
from .cipher import decrypt_private_key, aes_decrypt_base64
from .models import Account, Field, Share
from .exceptions import (
    LastPassException,
    LoginFailedException,
    AccountNotFoundException,
    InvalidSessionException,
)


class LastPassClient:
    """
    Main LastPass client for vault operations
    
    Example:
        # Login
        client = LastPassClient()
        client.login("user@example.com", "masterpassword")
        
        # List accounts
        accounts = client.get_accounts()
        
        # Find account
        account = client.find_account("github")
        print(account.username, account.password)
        
        # Add account
        client.add_account("New Site", "username", "password", url="https://example.com")
        
        # Logout
        client.logout()
    """
    
    def __init__(self, server: str = "lastpass.com", config_dir: Optional[Path] = None):
        """
        Initialize LastPass client
        
        Args:
            server: LastPass server hostname
            config_dir: Configuration directory (defaults to ~/.config/lpass)
        """
        self.server = server
        self.http = HTTPClient(server)
        self.session: Optional[Session] = None
        self.decryption_key: Optional[bytes] = None
        self.config_dir = config_dir or Session._get_config_dir()
        self._accounts: List[Account] = []
        self._shares: List[Share] = []
        self._blob_loaded = False
    
    def login(self, username: str, password: Optional[str] = None, 
              trust: bool = False, otp: Optional[str] = None,
              force: bool = False) -> None:
        """
        Login to LastPass
        
        Args:
            username: LastPass username/email
            password: Master password (will prompt if not provided)
            trust: Trust this device
            otp: One-time password for 2FA
            force: Force new login even if session exists
        
        Raises:
            LoginFailedException: If authentication fails
        """
        # Check for existing session
        if not force:
            existing_session = self._try_load_session(username, password)
            if existing_session:
                return
        
        # Get password if not provided
        if password is None:
            password = getpass("Master Password: ")
        
        # Get iteration count
        iterations = self.http.get_iterations(username)
        
        # Derive keys
        login_key, decryption_key = derive_keys(username, password, iterations)
        
        # Login to server
        response_xml, status = self.http.login(username, login_key, iterations, trust, otp)
        
        if status != 200:
            raise LoginFailedException(f"Login failed with HTTP status {status}")
        
        # Parse session from response
        self.session = parse_login_response(response_xml)
        self.session.server = self.server
        self.decryption_key = decryption_key
        
        # Decrypt private key if present
        if self.session.private_key:
            try:
                pem_key = decrypt_private_key(self.session.private_key, decryption_key)
                self.session.private_key = pem_key
            except Exception:
                # Private key decryption failed, but we can continue
                pass
        
        # Save session
        self.session.save(decryption_key, self.config_dir)
        
        # Reset blob cache
        self._blob_loaded = False
        self._accounts = []
        self._shares = []
    
    def _try_load_session(self, username: str, password: Optional[str]) -> bool:
        """Try to load existing session"""
        if password:
            iterations = self.http.get_iterations(username)
            _, decryption_key = derive_keys(username, password, iterations)
        else:
            # Try to load plaintext key
            plaintext_key_file = self.config_dir / "plaintext_key"
            if plaintext_key_file.exists():
                decryption_key = plaintext_key_file.read_bytes()
            else:
                return False
        
        session = Session.load(decryption_key, self.config_dir)
        
        if session and session.is_valid():
            self.session = session
            self.decryption_key = decryption_key
            self._blob_loaded = False
            return True
        
        return False
    
    def logout(self, force: bool = False) -> None:
        """
        Logout and clear session
        
        Args:
            force: Force logout even if server request fails
        """
        if self.session:
            try:
                self.http.logout(self.session)
            except Exception:
                if not force:
                    raise
        
        # Delete session file
        Session.kill(self.config_dir)
        
        # Clear in-memory data
        self.session = None
        self.decryption_key = None
        self._accounts = []
        self._shares = []
        self._blob_loaded = False
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self.session is not None and self.session.is_valid()
    
    def sync(self, force: bool = False) -> None:
        """
        Sync vault from server
        
        Args:
            force: Force sync even if already loaded
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        if self._blob_loaded and not force:
            return
        
        # Download blob
        blob_data = self.http.download_blob(self.session)
        
        # Parse blob
        accounts, shares = parse_blob(blob_data, self.decryption_key)
        
        self._accounts = accounts
        self._shares = shares
        self._blob_loaded = True
    
    def get_accounts(self, sync: bool = True) -> List[Account]:
        """
        Get all accounts from vault
        
        Args:
            sync: Sync from server before returning
        
        Returns:
            List of Account objects
        """
        if sync:
            self.sync()
        
        return self._accounts.copy()
    
    def get_shares(self, sync: bool = True) -> List[Share]:
        """
        Get all shared folders
        
        Args:
            sync: Sync from server before returning
        
        Returns:
            List of Share objects
        """
        if sync:
            self.sync()
        
        return self._shares.copy()
    
    def find_account(self, query: str, sync: bool = True) -> Optional[Account]:
        """
        Find a single account by name, ID, or URL
        
        Args:
            query: Search query (name, ID, or URL)
            sync: Sync from server before searching
        
        Returns:
            Account object or None if not found
        
        Raises:
            AccountNotFoundException: If multiple matches found
        """
        matches = self.search_accounts(query, sync=sync)
        
        if not matches:
            return None
        
        if len(matches) > 1:
            names = [a.fullname for a in matches]
            raise AccountNotFoundException(
                f"Multiple accounts match '{query}': {', '.join(names)}"
            )
        
        return matches[0]
    
    def search_accounts(self, query: str, sync: bool = True, 
                       group: Optional[str] = None) -> List[Account]:
        """
        Search for accounts
        
        Args:
            query: Search query (matches name, username, URL, ID)
            sync: Sync from server before searching
            group: Filter by group/folder
        
        Returns:
            List of matching accounts
        """
        if sync:
            self.sync()
        
        matches = []
        query_lower = query.lower()
        
        for account in self._accounts:
            # Filter by group if specified
            if group and account.group != group:
                continue
            
            # Check for exact ID match
            if account.id == query:
                return [account]
            
            # Check for substring matches
            if (query_lower in account.name.lower() or
                query_lower in account.fullname.lower() or
                query_lower in account.username.lower() or
                query_lower in account.url.lower()):
                matches.append(account)
        
        return matches
    
    def list_groups(self, sync: bool = True) -> List[str]:
        """
        Get list of all groups/folders
        
        Args:
            sync: Sync from server before listing
        
        Returns:
            List of group names
        """
        if sync:
            self.sync()
        
        groups = set()
        for account in self._accounts:
            if account.group:
                groups.add(account.group)
        
        return sorted(groups)
    
    def generate_password(self, length: int = 16, symbols: bool = True) -> str:
        """
        Generate a random password
        
        Args:
            length: Password length
            symbols: Include symbols
        
        Returns:
            Generated password
        """
        chars = string.ascii_letters + string.digits
        if symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def get_password(self, query: str, sync: bool = True) -> str:
        """
        Get password for an account
        
        Args:
            query: Account query
            sync: Sync before searching
        
        Returns:
            Password string
        
        Raises:
            AccountNotFoundException: If account not found
        """
        account = self.find_account(query, sync)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        return account.password
    
    def get_username(self, query: str, sync: bool = True) -> str:
        """
        Get username for an account
        
        Args:
            query: Account query
            sync: Sync before searching
        
        Returns:
            Username string
        
        Raises:
            AccountNotFoundException: If account not found
        """
        account = self.find_account(query, sync)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        return account.username
    
    def get_notes(self, query: str, sync: bool = True) -> str:
        """
        Get notes for an account
        
        Args:
            query: Account query
            sync: Sync before searching
        
        Returns:
            Notes string
        
        Raises:
            AccountNotFoundException: If account not found
        """
        account = self.find_account(query, sync)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        return account.notes
    
    def add_account(self, name: str, username: str = "", password: str = "",
                   url: str = "", notes: str = "", group: str = "",
                   fields: Optional[Dict[str, str]] = None) -> str:
        """
        Add a new account to the vault
        
        Args:
            name: Account name
            username: Username/email
            password: Password
            url: Website URL
            notes: Notes
            group: Group/folder name
            fields: Custom fields as dict
        
        Returns:
            Account ID of created account
        
        Raises:
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        from . import cipher
        
        # Encrypt account data
        account_data = {
            "name": cipher.aes_encrypt(name, self.encryption_key).decode('utf-8'),
            "username": cipher.aes_encrypt(username, self.encryption_key).decode('utf-8') if username else "",
            "password": cipher.aes_encrypt(password, self.encryption_key).decode('utf-8') if password else "",
            "url": cipher.aes_encrypt(url, self.encryption_key).decode('utf-8') if url else "",
            "extra": cipher.aes_encrypt(notes, self.encryption_key).decode('utf-8') if notes else "",
            "grouping": cipher.aes_encrypt(group, self.encryption_key).decode('utf-8') if group else "",
        }
        
        # Add custom fields if provided
        if fields:
            for field_name, field_value in fields.items():
                encrypted_name = cipher.aes_encrypt(field_name, self.encryption_key).decode('utf-8')
                encrypted_value = cipher.aes_encrypt(field_value, self.encryption_key).decode('utf-8')
                account_data[f"customfield_{encrypted_name}"] = encrypted_value
        
        account_id = self.http.add_account(self.session, account_data)
        
        # Sync to refresh vault
        self.sync(force=True)
        
        return account_id
    
    def update_account(self, query: str, name: Optional[str] = None,
                      username: Optional[str] = None, password: Optional[str] = None,
                      url: Optional[str] = None, notes: Optional[str] = None,
                      group: Optional[str] = None) -> None:
        """
        Update an existing account
        
        Args:
            query: Account query (name, ID, or URL)
            name: New name (if provided)
            username: New username (if provided)
            password: New password (if provided)
            url: New URL (if provided)
            notes: New notes (if provided)
            group: New group (if provided)
        
        Raises:
            AccountNotFoundException: If account not found
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        account = self.find_account(query, sync=True)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        
        from . import cipher
        
        # Build update data with only changed fields
        account_data = {}
        
        if name is not None:
            account_data["name"] = cipher.aes_encrypt(name, self.encryption_key).decode('utf-8')
        if username is not None:
            account_data["username"] = cipher.aes_encrypt(username, self.encryption_key).decode('utf-8')
        if password is not None:
            account_data["password"] = cipher.aes_encrypt(password, self.encryption_key).decode('utf-8')
        if url is not None:
            account_data["url"] = cipher.aes_encrypt(url, self.encryption_key).decode('utf-8')
        if notes is not None:
            account_data["extra"] = cipher.aes_encrypt(notes, self.encryption_key).decode('utf-8')
            if group is not None:
                account_data["grouping"] = cipher.aes_encrypt(group, self.encryption_key).decode('utf-8')
        
        self.http.update_account(self.session, account.id, account_data)
        
        # Sync to refresh vault
        self.sync(force=True)
    
    def delete_account(self, query: str) -> None:
        """
        Delete an account from the vault
        
        Args:
            query: Account query (name, ID, or URL)
        
        Raises:
            AccountNotFoundException: If account not found
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        account = self.find_account(query, sync=True)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        
        share_id = account.share.id if account.share else None
        self.http.delete_account(self.session, account.id, share_id)
        
        # Sync to refresh vault
        self.sync(force=True)
    
    def duplicate_account(self, query: str, new_name: Optional[str] = None) -> str:
        """
        Duplicate an existing account
        
        Args:
            query: Account query (name, ID, or URL)
            new_name: Name for the duplicate (defaults to "Copy of [original name]")
        
        Returns:
            Account ID of duplicated account
        
        Raises:
            AccountNotFoundException: If account not found
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        account = self.find_account(query, sync=True)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        
        # Generate new name if not provided
        if new_name is None:
            new_name = f"Copy of {account.name}"
        
        # Create duplicate with same data
        fields = {}
        if account.fields:
            for field in account.fields:
                fields[field.name] = field.value
        
        return self.add_account(
            name=new_name,
            username=account.username,
            password=account.password,
            url=account.url,
            notes=account.notes,
            group=account.group,
            fields=fields
        )
    
    def move_account(self, query: str, new_group: str) -> None:
        """
        Move an account to a different group/folder
        
        Args:
            query: Account query (name, ID, or URL)
            new_group: New group/folder name
        
        Raises:
            AccountNotFoundException: If account not found
            InvalidSessionException: If not logged in
        """
        self.update_account(query, group=new_group)
