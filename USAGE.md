# Usage Guide

This guide provides comprehensive examples for using lastpass-py both as a CLI tool and as a Python library.

## Table of Contents

- [Command Line Interface](#command-line-interface)
- [Python API](#python-api)
- [Advanced Usage](#advanced-usage)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)

## Command Line Interface

### Authentication

```bash
# Login to LastPass
lpass login user@example.com

# Login with trust (for 30 days)
lpass login --trust user@example.com

# Login with MFA/OTP
lpass login user@example.com
# (will prompt for OTP code)

# Check login status
lpass status

# Logout
lpass logout

# Force logout (even if errors)
lpass logout --force
```

### Viewing Accounts

```bash
# List all accounts
lpass ls

# List accounts in a specific group
lpass ls Work/

# Show account details
lpass show GitHub

# Show specific field
lpass show GitHub --password
lpass show GitHub --username
lpass show GitHub --url
lpass show GitHub --notes

# Show custom field
lpass show GitHub --field="API Key"

# Output in JSON format
lpass show GitHub --json

# Copy to clipboard
lpass show GitHub --password --clip

# Custom formatting
lpass show GitHub --format="%an: %au @ %al"
lpass ls --format="%/ag%an - %au"
```

### Managing Accounts

```bash
# Add a new account
lpass add GitHub
# (opens editor)

# Add with command-line fields
lpass add GitHub --username=user --password=pass --url=https://github.com

# Add with password generation
lpass add GitHub --username=user --generate --url=https://github.com

# Edit an account
lpass edit GitHub

# Move account to group
lpass mv GitHub Work/GitHub

# Duplicate an account
lpass duplicate GitHub GitHub-backup

# Delete an account
lpass rm GitHub

# Delete without confirmation
lpass rm GitHub --force
```

### Password Generation

```bash
# Generate 20 character password
lpass generate 20

# Generate and copy to clipboard
lpass generate 20 --clip

# Generate without symbols
lpass generate 20 --no-symbols

# Generate for existing account
lpass generate GitHub 20
```

### Sync and Export

```bash
# Force sync with server
lpass sync

# Export to CSV
lpass export > passwords.csv

# Export specific fields
lpass export --fields=url,username,password

# Import from CSV
lpass import passwords.csv

# Skip duplicates during import
lpass import --skip-duplicates passwords.csv
```

### Secure Notes

```bash
# Add a secure note (generic)
lpass add-note "Credit Card" < note.txt

# Add specific note types
lpass add-note --note-type=credit-card "My Visa"
lpass add-note --note-type=ssh-key "Production Server"
lpass add-note --note-type=bank-account "Checking"

# Available note types:
# - generic
# - credit-card
# - bank-account
# - ssh-key
# - server
# - database
# - drivers-license
# - wifi-password
```

### Sharing (Enterprise Feature)

```bash
# List shares
lpass share ls

# Create a share
lpass share create TeamPasswords

# Add user to share
lpass share add TeamPasswords user@example.com --read-only

# Remove user from share
lpass share rm TeamPasswords user@example.com

# Delete a share
lpass share delete TeamPasswords
```

## Python API

### Basic Usage

```python
from lastpass import LastPassClient

# Create client
client = LastPassClient()

# Login
client.login("user@example.com", "password")

# Check if logged in
if client.is_logged_in():
    print("Logged in successfully!")

# Get all accounts
accounts = client.get_accounts()
for account in accounts:
    print(f"{account.name}: {account.username}")

# Logout
client.logout()
```

### Working with Accounts

```python
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "password")

# Find specific account
account = client.find_account("GitHub")
if account:
    print(f"Username: {account.username}")
    print(f"Password: {account.password}")
    print(f"URL: {account.url}")
    print(f"Notes: {account.notes}")

# Search accounts
results = client.search_accounts("github")
for account in results:
    print(f"Found: {account.name}")

# Advanced search with regex
import re
pattern = re.compile(r"^git", re.IGNORECASE)
results = client.search_accounts_regex(pattern)

# Search in specific fields
results = client.search_accounts_advanced(
    "api",
    fields=["name", "notes"]
)

# List groups
groups = client.list_groups()
print(f"Groups: {', '.join(groups)}")
```

### Adding and Modifying Accounts

```python
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "password")

# Add a new account
client.add_account(
    name="GitHub",
    username="myuser",
    password="secretpass123",
    url="https://github.com",
    group="Work",
    notes="Personal GitHub account"
)

# Add account with custom fields
client.add_account(
    name="AWS",
    username="admin",
    password="pass",
    fields=[
        {"name": "Access Key", "value": "AKIAIOSFODNN7EXAMPLE"},
        {"name": "Secret Key", "value": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"}
    ]
)

# Update an account
client.update_account(
    "GitHub",
    username="newuser",
    password="newpass456",
    notes="Updated notes"
)

# Move account to different group
client.move_account("GitHub", "Personal/GitHub")

# Duplicate an account
client.duplicate_account("GitHub", "GitHub-backup")

# Delete an account
client.delete_account("GitHub")
```

### Password Generation

```python
from lastpass import LastPassClient

client = LastPassClient()

# Generate password (no login required)
password = client.generate_password(length=20, symbols=True)
print(f"Generated: {password}")

# Generate without symbols
password = client.generate_password(length=16, symbols=False)

# Generate and update existing account
password = client.generate_password(length=24)
client.login("user@example.com", "mypass")
client.update_account("GitHub", password=password)
```

### Working with Secure Notes

```python
from lastpass import LastPassClient
from lastpass.note_types import NoteType

client = LastPassClient()
client.login("user@example.com", "password")

# Add a generic note
client.add_secure_note(
    name="Important Info",
    content="My secure note content",
    note_type=NoteType.GENERIC
)

# Add a credit card note
client.add_secure_note(
    name="My Visa",
    fields={
        "Number": "4111111111111111",
        "Expiry": "12/25",
        "CVV": "123",
        "Name on Card": "John Doe"
    },
    note_type=NoteType.CREDIT_CARD
)

# Add an SSH key note
client.add_secure_note(
    name="Production Server",
    fields={
        "Hostname": "prod.example.com",
        "Username": "root",
        "Private Key": "-----BEGIN RSA PRIVATE KEY-----\n...",
        "Public Key": "ssh-rsa AAAAB3..."
    },
    note_type=NoteType.SSH_KEY
)
```

### Import/Export

```python
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "password")

# Export to CSV string
csv_data = client.export_to_csv()
print(csv_data)

# Export to file
with open("export.csv", "w") as f:
    f.write(csv_data)

# Export specific fields
csv_data = client.export_to_csv(
    fields=["name", "url", "username", "password", "notes"]
)

# Import from CSV file
with open("import.csv", "r") as f:
    csv_data = f.read()

accounts_imported = client.import_from_csv(
    csv_data,
    skip_duplicates=True  # Skip accounts that already exist
)
print(f"Imported {len(accounts_imported)} accounts")
```

### Working with Shares (Enterprise)

```python
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "password")

# Get all shares
shares = client.get_shares()
for share in shares:
    print(f"Share: {share.name} (ID: {share.id})")

# Find a specific share
share = client.find_share("TeamPasswords")

# Create a new share
client.create_share("DevelopmentTeam")

# Add user to share
client.add_share_user(
    "DevelopmentTeam",
    "developer@example.com",
    readonly=False,
    give=True,  # Can share with others
    admin=False
)

# List users in a share
users = client.list_share_users("DevelopmentTeam")
for user in users:
    print(f"User: {user['email']}, Permissions: {user['permissions']}")

# Update user permissions
client.update_share_user(
    "DevelopmentTeam",
    "developer@example.com",
    readonly=True  # Make read-only
)

# Remove user from share
client.remove_share_user("DevelopmentTeam", "developer@example.com")

# Delete a share
client.delete_share("DevelopmentTeam")
```

### Attachments

```python
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "password")

# Get account with attachments
account = client.find_account("Important Docs")
if account.attachments:
    for attachment in account.attachments:
        print(f"Attachment: {attachment.filename}")

# Download an attachment
account = client.find_account("Important Docs")
if account.attachments:
    attachment = account.attachments[0]
    data = client.get_attachment(account, attachment)
    
    # Save to file
    with open(attachment.filename, "wb") as f:
        f.write(data)

# Upload an attachment
with open("document.pdf", "rb") as f:
    data = f.read()

client.upload_attachment(
    account,
    filename="document.pdf",
    data=data
)
```

## Advanced Usage

### Session Persistence

```python
from lastpass import LastPassClient

client = LastPassClient()

# Login and save session
client.login("user@example.com", "password")
# Session automatically saved to ~/.lpass/

# Later, in another script:
client2 = LastPassClient()
# Session automatically loaded
if client2.is_logged_in():
    accounts = client2.get_accounts()
```

### Custom Configuration

```python
from lastpass import LastPassClient, Config

# Custom configuration directory
client = LastPassClient(config_dir="/custom/path")

# Custom server (for Enterprise)
client = LastPassClient(server="https://lastpass.company.com")

# Access configuration
config = Config()
config.set("color", "always")
alias = config.get_alias("github")
```

### Batch Operations

```python
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "password")

# Batch add multiple accounts
accounts_data = [
    {"name": "Site1", "username": "user1", "password": "pass1"},
    {"name": "Site2", "username": "user2", "password": "pass2"},
    {"name": "Site3", "username": "user3", "password": "pass3"},
]

client.batch_add_accounts(accounts_data)
```

## Error Handling

### Common Exceptions

```python
from lastpass import LastPassClient
from lastpass.exceptions import (
    LastPassException,
    LoginFailedException,
    InvalidSessionException,
    NetworkException,
    AccountNotFoundException,
    DecryptionException
)

client = LastPassClient()

try:
    client.login("user@example.com", "wrong_password")
except LoginFailedException as e:
    print(f"Login failed: {e}")
except NetworkException as e:
    print(f"Network error: {e}")
except LastPassException as e:
    print(f"LastPass error: {e}")

try:
    account = client.find_account("NonExistent")
    if account is None:
        print("Account not found")
except InvalidSessionException:
    print("Not logged in or session expired")
    client.login("user@example.com", "password")
```

## Best Practices

### 1. Use Context Managers (if available)

```python
# Good: Ensures logout on exit
from lastpass import LastPassClient

def main():
    client = LastPassClient()
    try:
        client.login("user@example.com", "password")
        accounts = client.get_accounts()
        # ... do work ...
    finally:
        client.logout()
```

### 2. Check Login Status

```python
# Always verify login before operations
if not client.is_logged_in():
    client.login("user@example.com", "password")

accounts = client.get_accounts()
```

### 3. Handle Sync Properly

```python
# Force sync for fresh data
client.sync(force=True)
accounts = client.get_accounts()

# Or pass sync parameter
accounts = client.get_accounts(sync=True)
```

### 4. Use Environment Variables for Credentials

```python
import os
from lastpass import LastPassClient

client = LastPassClient()
username = os.environ.get("LASTPASS_USERNAME")
password = os.environ.get("LASTPASS_PASSWORD")

if username and password:
    client.login(username, password)
```

### 5. Secure Password Handling

```python
import getpass
from lastpass import LastPassClient

client = LastPassClient()

# Prompt securely
username = input("Email: ")
password = getpass.getpass("Master Password: ")

client.login(username, password)
```

## API Reference

### LastPassClient

**Constructor**: `LastPassClient(server: str = None, config_dir: str = None)`

**Authentication Methods**:
- `login(username: str, password: str, otp: str = None, trust: bool = False) -> Session`
- `logout(force: bool = False) -> None`
- `is_logged_in() -> bool`

**Account Methods**:
- `get_accounts(sync: bool = False) -> List[Account]`
- `find_account(name_or_id: str) -> Optional[Account]`
- `search_accounts(query: str) -> List[Account]`
- `search_accounts_regex(pattern: Pattern, fields: List[str] = None) -> List[Account]`
- `search_accounts_advanced(query: str, fields: List[str] = None) -> List[Account]`
- `add_account(name: str, username: str = "", password: str = "", url: str = "", group: str = "", notes: str = "", fields: List[Dict] = None) -> Account`
- `update_account(name_or_id: str, **kwargs) -> Account`
- `delete_account(name_or_id: str) -> None`
- `duplicate_account(name_or_id: str, new_name: str = None) -> Account`
- `move_account(name_or_id: str, group: str) -> Account`

**Password Methods**:
- `generate_password(length: int = 20, symbols: bool = True) -> str`
- `get_password(name_or_id: str) -> str`
- `get_username(name_or_id: str) -> str`
- `get_notes(name_or_id: str) -> str`

**Group Methods**:
- `list_groups(sync: bool = False) -> List[str]`

**Import/Export Methods**:
- `export_to_csv(fields: List[str] = None) -> str`
- `import_from_csv(csv_data: str, skip_duplicates: bool = False) -> List[Account]`

**Share Methods (Enterprise)**:
- `get_shares(sync: bool = False) -> List[Share]`
- `find_share(name: str) -> Optional[Share]`
- `create_share(name: str) -> Share`
- `delete_share(name: str) -> None`
- `add_share_user(share_name: str, email: str, readonly: bool = True, give: bool = False, admin: bool = False) -> None`
- `remove_share_user(share_name: str, email: str) -> None`
- `update_share_user(share_name: str, email: str, **permissions) -> None`
- `list_share_users(share_name: str) -> List[Dict]`

**Attachment Methods**:
- `get_attachment(account: Account, attachment: Attachment) -> bytes`
- `upload_attachment(account: Account, filename: str, data: bytes) -> None`

**Sync Methods**:
- `sync(force: bool = False) -> None`

### Account Model

**Attributes**:
- `id: str` - Account ID
- `name: str` - Account name
- `username: str` - Username
- `password: str` - Password
- `url: str` - URL
- `notes: str` - Notes
- `group: str` - Group/folder path
- `share: Optional[Share]` - Associated share (if in shared folder)
- `fields: List[Field]` - Custom fields
- `attachments: List[Attachment]` - File attachments

**Methods**:
- `to_dict() -> Dict` - Convert to dictionary

### Exceptions

- `LastPassException` - Base exception
- `LoginFailedException` - Login failed (wrong credentials)
- `InvalidSessionException` - Session expired or not logged in
- `NetworkException` - Network/HTTP error
- `AccountNotFoundException` - Account not found
- `DecryptionException` - Decryption failed
- `InvalidPasswordException` - Invalid password format
- `ConfigurationException` - Configuration error
- `ValidationException` - Input validation error

## Environment Variables

- `LASTPASS_USERNAME` - Default username for login
- `LASTPASS_PASSWORD` - Default password (use with caution!)
- `LPASS_HOME` - Custom configuration directory (default: `~/.lpass`)
- `LPASS_AGENT_TIMEOUT` - SSH agent timeout in seconds
- `LPASS_CLIPBOARD_COMMAND` - Custom clipboard command
- `LPASS_DISABLE_PINENTRY` - Disable pinentry dialogs (1 to disable)

## See Also

- [Installation Guide](INSTALL.md)
- [Development Guide](DEVELOPMENT.md)
- [Contributing Guide](CONTRIBUTING.md)
- [LastPass CLI (C)](https://github.com/lastpass/lastpass-cli) - Original implementation
