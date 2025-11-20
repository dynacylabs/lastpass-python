"""
Main LastPass client with friendly Python API
"""

import os
import re
import secrets
import string
from pathlib import Path
from typing import List, Optional, Dict, Any, TextIO
from getpass import getpass

from .session import Session
from .http import HTTPClient
from .kdf import derive_keys
from .blob import parse_blob
from .xml_parser import parse_login_response
from .cipher import decrypt_private_key, aes_decrypt_base64
from .models import Account, Field, Share, ShareLimit
from .note_types import NoteType
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
    
    @property
    def encryption_key(self) -> Optional[bytes]:
        """Encryption key (same as decryption key in LastPass)"""
        return self.decryption_key
    
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
                   fields: Optional[Dict[str, str]] = None, is_app: bool = False) -> str:
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
            is_app: Whether this is an application entry
        
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
        
        # Mark as application entry if specified
        if is_app:
            account_data["appname"] = cipher.aes_encrypt(name, self.encryption_key).decode('utf-8')
        
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
                      group: Optional[str] = None, fields: Optional[Dict[str, str]] = None) -> None:
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
            fields: Custom fields as dict (if provided)
        
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
        
        # Add custom fields if provided
        if fields:
            for field_name, field_value in fields.items():
                encrypted_name = cipher.aes_encrypt(field_name, self.encryption_key).decode('utf-8')
                encrypted_value = cipher.aes_encrypt(field_value, self.encryption_key).decode('utf-8')
                account_data[f"customfield_{encrypted_name}"] = encrypted_value
        
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
    
    def get_attachment(self, query: str, attachment_id: str) -> bytes:
        """
        Download an attachment from an account
        
        Args:
            query: Account query (name, ID, or URL)
            attachment_id: Attachment ID
        
        Returns:
            Attachment data as bytes
        
        Raises:
            AccountNotFoundException: If account not found
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        account = self.find_account(query, sync=True)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        
        # Get share ID if account is in a shared folder
        share_id = account.share.id if account.share else None
        
        # Decrypt attachment using http module
        from . import cipher
        
        encrypted_data = self.http.get_attachment(self.session, attachment_id, share_id)
        
        # The attachment data comes back encrypted
        decrypted_data = cipher.decrypt_aes256_cbc_base64(
            encrypted_data.decode('utf-8'),
            self.encryption_key
        )
        
        return decrypted_data
    
    def upload_attachment(self, query: str, filename: str, file_data: bytes) -> None:
        """
        Upload an attachment to an account
        
        Args:
            query: Account query (name, ID, or URL)
            filename: Name of the file
            file_data: File data as bytes
        
        Raises:
            AccountNotFoundException: If account not found
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        account = self.find_account(query, sync=True)
        if not account:
            raise AccountNotFoundException(f"Account not found: {query}")
        
        # Get share ID if account is in a shared folder
        share_id = account.share.id if account.share else None
        
        # Encrypt attachment data
        from . import cipher
        encrypted_data = cipher.aes_encrypt(file_data, self.encryption_key)
        
        # Upload using http module
        self.http.upload_attachment(self.session, account.id, filename, 
                                    encrypted_data, share_id)
        
        # Sync to refresh vault
        self.sync(force=True)
    
    def search_accounts_advanced(self, query: str, search_type: str = 'exact',
                                 fields: Optional[List[str]] = None,
                                 sync: bool = True) -> List[Account]:
        """
        Advanced account search with regex and substring support
        
        Args:
            query: Search query
            search_type: 'exact', 'regex', or 'substring'
            fields: List of fields to search ('id', 'name', 'fullname', 'url', 'username')
            sync: Sync from server before searching
        
        Returns:
            List of matching accounts
        """
        import re
        
        if sync:
            self.sync()
        
        if fields is None:
            fields = ['name', 'id', 'fullname']
        
        matches = []
        
        for account in self._accounts:
            if search_type == 'exact':
                # Exact match on any field
                for field in fields:
                    field_value = getattr(account, field, '')
                    if field_value == query:
                        matches.append(account)
                        break
            
            elif search_type == 'regex':
                # Regex match
                try:
                    pattern = re.compile(query, re.IGNORECASE)
                    for field in fields:
                        field_value = getattr(account, field, '')
                        if pattern.search(field_value):
                            matches.append(account)
                            break
                except re.error:
                    # Invalid regex, fall back to substring
                    pass
            
            elif search_type == 'substring':
                # Substring match (case insensitive)
                query_lower = query.lower()
                for field in fields:
                    field_value = getattr(account, field, '').lower()
                    if query_lower in field_value:
                        matches.append(account)
                        break
        
        return matches
    
    def get_share_limits(self, share_name: str, username: str) -> Optional[ShareLimit]:
        """
        Get access limits for a user in a shared folder
        
        Args:
            share_name: Shared folder name or ID
            username: Username to get limits for
        
        Returns:
            ShareLimit object with whitelist/blacklist and account IDs
        
        Raises:
            InvalidSessionException: If not logged in
            AccountNotFoundException: If share not found
        """
        from .models import ShareLimit
        
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        # Find share
        shares = self.get_shares(sync=True)
        share = None
        for s in shares:
            if s.id == share_name or s.name == share_name:
                share = s
                break
        
        if not share:
            raise AccountNotFoundException(f"Share not found: {share_name}")
        
        # Get user ID - this requires getting share user info
        # For now, use username as user_id (the HTTP layer should handle this)
        user_id = username
        
        # Get limits from server
        try:
            whitelist, account_ids = self.http.get_share_limits(
                self.session, share.id, user_id
            )
            return ShareLimit(whitelist=whitelist, account_ids=account_ids)
        except Exception as e:
            # Limits not set or error
            return None
    
    def set_share_limits(self, share_name: str, username: str, 
                        limit: ShareLimit) -> None:
        """
        Set access limits for a user in a shared folder
        
        Args:
            share_name: Shared folder name or ID
            username: Username to set limits for
            limit: ShareLimit object with whitelist/blacklist and account IDs
        
        Raises:
            InvalidSessionException: If not logged in
            AccountNotFoundException: If share not found
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        # Find share
        shares = self.get_shares(sync=True)
        share = None
        for s in shares:
            if s.id == share_name or s.name == share_name:
                share = s
                break
        
        if not share:
            raise AccountNotFoundException(f"Share not found: {share_name}")
        
        # Get user ID
        user_id = username
        
        # Set limits on server
        self.http.set_share_limits(
            self.session, share.id, user_id,
            limit.whitelist, limit.account_ids
        )
    
    def find_share(self, query: str, sync: bool = True) -> Optional[Share]:
        """
        Find a shared folder by name or ID
        
        Args:
            query: Share name or ID
            sync: Sync from server before searching
        
        Returns:
            Share object or None if not found
        """
        if sync:
            self.sync()
        
        for share in self._shares:
            if share.id == query or share.name == query:
                return share
        
        return None
    
    def search_accounts_regex(self, query: str, sync: bool = True) -> List[Account]:
        """
        Search accounts using regex pattern
        
        Args:
            query: Regex pattern
            sync: Sync from server before searching
        
        Returns:
            List of matching accounts
        """
        return self.search_accounts_advanced(query, search_type='regex', sync=sync)
    
    def search_accounts_fixed(self, query: str, sync: bool = True) -> List[Account]:
        """
        Search accounts using fixed string (substring) matching
        
        Args:
            query: Search string
            sync: Sync from server before searching
        
        Returns:
            List of matching accounts
        """
        return self.search_accounts_advanced(query, search_type='substring', sync=sync)
    
    def create_share(self, share_name: str) -> str:
        """
        Create a new shared folder
        
        Args:
            share_name: Name of the shared folder to create
        
        Returns:
            Share ID as string
        
        Raises:
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        share_id = self.http.create_share(self.session, share_name)
        
        # Sync to refresh vault
        self.sync(force=True)
        
        return share_id
    
    def delete_share(self, share_name_or_id: str) -> None:
        """
        Delete a shared folder
        
        Args:
            share_name_or_id: Share name or ID
        
        Raises:
            InvalidSessionException: If not logged in
            AccountNotFoundException: If share not found
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        # Find share
        share = self.find_share(share_name_or_id, sync=True)
        if not share:
            raise AccountNotFoundException(f"Share not found: {share_name_or_id}")
        
        self.http.delete_share(self.session, share.id)
        
        # Sync to refresh vault
        self.sync(force=True)
    
    def list_share_users(self, share_name_or_id: str) -> List[Dict[str, Any]]:
        """
        List users who have access to a shared folder
        
        Args:
            share_name_or_id: Share name or ID
        
        Returns:
            List of user dictionaries with keys: username, readonly, admin, hide_passwords, etc.
        
        Raises:
            InvalidSessionException: If not logged in
            AccountNotFoundException: If share not found
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        # Find share
        share = self.find_share(share_name_or_id, sync=True)
        if not share:
            raise AccountNotFoundException(f"Share not found: {share_name_or_id}")
        
        return self.http.get_share_users(self.session, share.id)
    
    def add_share_user(self, share_name_or_id: str, username: str,
                      readonly: bool = False, admin: bool = False,
                      hide_passwords: bool = False) -> None:
        """
        Add a user to a shared folder
        
        Args:
            share_name_or_id: Share name or ID
            username: Username/email to add
            readonly: Grant read-only access
            admin: Grant admin privileges
            hide_passwords: Hide passwords from user
        
        Raises:
            InvalidSessionException: If not logged in
            AccountNotFoundException: If share not found
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        # Find share
        share = self.find_share(share_name_or_id, sync=True)
        if not share:
            raise AccountNotFoundException(f"Share not found: {share_name_or_id}")
        
        self.http.add_share_user(
            self.session, share.id, username,
            readonly=readonly, admin=admin, hide_passwords=hide_passwords
        )
        
        # Sync to refresh vault
        self.sync(force=True)
    
    def remove_share_user(self, share_name_or_id: str, username: str) -> None:
        """
        Remove a user from a shared folder
        
        Args:
            share_name_or_id: Share name or ID
            username: Username/email to remove
        
        Raises:
            InvalidSessionException: If not logged in
            AccountNotFoundException: If share not found
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        # Find share
        share = self.find_share(share_name_or_id, sync=True)
        if not share:
            raise AccountNotFoundException(f"Share not found: {share_name_or_id}")
        
        self.http.remove_share_user(self.session, share.id, username)
        
        # Sync to refresh vault
        self.sync(force=True)
    
    def update_share_user(self, share_name_or_id: str, username: str,
                         readonly: Optional[bool] = None,
                         admin: Optional[bool] = None,
                         hide_passwords: Optional[bool] = None) -> None:
        """
        Update permissions for a user in a shared folder
        
        Args:
            share_name_or_id: Share name or ID
            username: Username/email to update
            readonly: Set read-only access (None = no change)
            admin: Set admin privileges (None = no change)
            hide_passwords: Hide passwords (None = no change)
        
        Raises:
            InvalidSessionException: If not logged in
            AccountNotFoundException: If share not found
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        # Find share
        share = self.find_share(share_name_or_id, sync=True)
        if not share:
            raise AccountNotFoundException(f"Share not found: {share_name_or_id}")
        
        self.http.update_share_user(
            self.session, share.id, username,
            readonly=readonly, admin=admin, hide_passwords=hide_passwords
        )
        
        # Sync to refresh vault
        self.sync(force=True)
    
    def change_password(self, current_password: str, new_password: str) -> None:
        """
        Change master password
        
        Args:
            current_password: Current master password
            new_password: New master password
        
        Raises:
            InvalidSessionException: If not logged in
            LoginFailedException: If current password is incorrect
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        if not self.session or not self.session.uid:
            raise InvalidSessionException("Session not properly initialized")
        
        username = self.session.uid
        
        # Get iteration counts
        old_iterations = self.http.get_iterations(username)
        
        # Derive old keys to verify
        old_login_key, old_decryption_key = derive_keys(username, current_password, old_iterations)
        
        # Verify current password is correct
        if old_decryption_key != self.decryption_key:
            raise LoginFailedException("Current password is incorrect")
        
        # Derive new keys (using same iteration count for now)
        new_login_key, new_decryption_key = derive_keys(username, new_password, old_iterations)
        
        # Start password change
        token = self.http.change_password_start(
            self.session, username, old_login_key, new_login_key, old_iterations
        )
        
        # Complete password change
        self.http.change_password_complete(
            self.session, username, new_login_key, old_iterations, token
        )
        
        # Update local decryption key
        self.decryption_key = new_decryption_key
        
        # Re-save session with new key
        self.session.save(new_decryption_key, self.config_dir)
    
    def export_to_csv(self, fields: Optional[List[str]] = None, 
                     output: Optional[TextIO] = None) -> str:
        """
        Export vault to CSV format
        
        Args:
            fields: List of field names to export (default: all standard fields)
            output: Optional file object to write to
        
        Returns:
            CSV string if output is None
        
        Raises:
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        from .csv_utils import export_accounts_to_csv
        
        # Get all accounts
        accounts = self.get_accounts(sync=True)
        
        # Export to CSV
        return export_accounts_to_csv(accounts, fields, output)
    
    def import_from_csv(self, csv_data: str, keep_duplicates: bool = False) -> int:
        """
        Import accounts from CSV format
        
        Args:
            csv_data: CSV string or file content
            keep_duplicates: Keep duplicate entries instead of skipping
        
        Returns:
            Number of accounts imported
        
        Raises:
            InvalidSessionException: If not logged in
        """
        if not self.is_logged_in():
            raise InvalidSessionException("Not logged in")
        
        from .csv_utils import import_accounts_from_csv
        
        # Parse CSV
        accounts_data = import_accounts_from_csv(csv_data, keep_duplicates)
        
        # Import each account
        count = 0
        for account_data in accounts_data:
            try:
                self.add_account(
                    name=account_data["name"],
                    username=account_data.get("username", ""),
                    password=account_data.get("password", ""),
                    url=account_data.get("url", ""),
                    notes=account_data.get("notes", ""),
                    group=account_data.get("group", ""),
                    fields=account_data.get("fields"),
                )
                count += 1
            except Exception:
                # Skip accounts that fail to import
                continue
        
        return count
    
    def add_secure_note(self, name: str, note_type: NoteType, 
                       fields: Dict[str, str], group: str = "") -> str:
        """
        Add a secure note with structured fields
        
        Args:
            name: Note name
            note_type: Type of secure note (from note_types module)
            fields: Dictionary of field names to values
            group: Group/folder name
        
        Returns:
            Account ID of created note
        
        Raises:
            InvalidSessionException: If not logged in
        """
        from .notes import notes_collapse
        from .models import Account
        
        # Create a temporary account with the secure note structure
        temp_account = Account(
            id="",
            name=name,
            username="",
            password="",
            url="http://sn",
            group=group,
            notes="",
            fullname=name,
            fields=[],
            attachments=[],
            share=None,
        )
        
        # Add NoteType field
        fields["NoteType"] = note_type.value
        
        # Use notes_collapse to format the note
        from .note_types import get_template
        template = get_template(note_type)
        
        # Build notes string
        notes_lines = [f"NoteType:{note_type.value}"]
        for field_name in template.fields:
            if field_name in fields:
                notes_lines.append(f"{field_name}:{fields[field_name]}")
        
        notes_str = "\n".join(notes_lines)
        
        return self.add_account(
            name=name,
            username="",
            password="",
            url="http://sn",
            notes=notes_str,
            group=group,
        )
