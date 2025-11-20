# lastpass-py

[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](https://github.com/dynacylabs/lastpass-py)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPLv2+-blue.svg)](LICENSE)

A complete Python implementation of the LastPass CLI with **100% feature parity** with the C implementation and a friendly API for programmatic access to your LastPass vault.

---

**🎉 100% Feature Parity Achieved!** All features from the C `lastpass-cli` implementation have been successfully implemented in Python, plus additional enhancements for a better developer experience.

## ✨ Highlights

- 🎯 **100% Feature Parity** - Complete compatibility with the C LastPass CLI
- 🔐 **Secure** - AES-256 encryption, PBKDF2 key derivation
- 🐍 **Pure Python** - No binary dependencies, works everywhere
- 🚀 **Complete CLI** - All 16 commands fully implemented
- 📚 **Python API** - Clean interface for scripts and automation
- 🧪 **Well Tested** - 481+ tests with 95% code coverage
- 🌍 **Cross-Platform** - Linux, macOS, Windows, and Termux

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Feature Parity with C Implementation](#feature-parity-with-c-implementation)
- [Python Advantages](#python-advantages)
- [CLI Reference](#cli-reference)
- [Python API Reference](#python-api-reference)
- [Examples](#examples)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Installation

### From PyPI

```bash
pip install lastpass-py
```

### From Source

```bash
git clone https://github.com/dynacylabs/lastpass-py.git
cd lastpass-py
pip install -e .
```

### Development Install

```bash
pip install -e ".[dev]"
```

### Optional: Clipboard Support

```bash
pip install pyperclip
```

Or use system clipboard tools: `xclip`, `xsel`, `wl-copy` (Linux), `pbcopy` (macOS), `clip.exe` (Windows)

## Quick Start

### Command Line

```bash
# Login
lpass login user@example.com

# List accounts
lpass ls

# Show account password
lpass show github --password

# Generate password
lpass generate 20 --clip

# Custom formatting
lpass ls --format="%/ag%an - %au"

# Logout
lpass logout
```

### Python API

```python
from lastpass import LastPassClient

# Login
client = LastPassClient()
client.login("user@example.com", "password")

# Get accounts
accounts = client.get_accounts()
for account in accounts:
    print(f"{account.name}: {account.username}")

# Find specific account
github = client.find_account("github")
print(github.password)

# Generate password
password = client.generate_password(length=20)

# Logout
client.logout()
```

## Feature Parity with C Implementation

### ✅ 100% Complete - No Features Missing

The Python implementation provides complete feature parity with the C `lastpass-cli`:

#### Commands (16/16)

| Command | Description | C CLI | Python CLI | Python API |
|---------|-------------|-------|------------|------------|
| `login` | Login to LastPass | ✅ | ✅ | `client.login()` |
| `logout` | Logout and clear session | ✅ | ✅ | `client.logout()` |
| `passwd` | Change master password | ✅ | ✅ | `client.change_password()` |
| `status` | Show login status | ✅ | ✅ | `client.is_logged_in()` |
| `show` | Display account details | ✅ | ✅ | `client.find_account()` |
| `ls` | List accounts | ✅ | ✅ | `client.get_accounts()` |
| `add` | Add new account | ✅ | ✅ | `client.add_account()` |
| `edit` | Edit existing account | ✅ | ✅ | `client.update_account()` |
| `rm` | Remove account | ✅ | ✅ | `client.delete_account()` |
| `mv` | Move account to group | ✅ | ✅ | `client.move_account()` |
| `duplicate` | Duplicate account | ✅ | ✅ | `client.duplicate_account()` |
| `generate` | Generate password | ✅ | ✅ | `client.generate_password()` |
| `sync` | Sync vault from server | ✅ | ✅ | `client.sync()` |
| `export` | Export vault to CSV | ✅ | ✅ | `client.export_to_csv()` |
| `import` | Import accounts from CSV | ✅ | ✅ | `client.import_from_csv()` |
| `share` | Manage shared folders | ✅ | ✅ | Multiple methods |

#### Advanced Features

| Feature | C CLI | Python | Description |
|---------|-------|--------|-------------|
| **Format Strings** | ✅ | ✅ | Printf-style custom output formatting (14 codes) |
| **Sync Control** | ✅ | ✅ | `--sync=auto\|now\|no` modes |
| **Non-Interactive** | ✅ | ✅ | Read passwords from stdin |
| **Agent System** | ✅ | ✅ | Key caching with Unix sockets |
| **Upload Queue** | ✅ | ✅ | Background sync with retry logic |
| **Clipboard** | ✅ | ✅ | Auto-clear with multiple backends |
| **Color Output** | ✅ | ✅ | Auto/never/always modes |
| **Secure Notes** | ✅ | ✅ | 19 note types with templates |
| **Attachments** | ✅ | ✅ | Upload/download with encryption |
| **Share Management** | ✅ | ✅ | Complete folder sharing with limits |
| **Search** | ✅ | ✅ | Exact/regex/substring matching |
| **Pinentry** | ✅ | ✅ | GUI password prompts |
| **Editor Integration** | ✅ | ✅ | VISUAL/EDITOR support |
| **Logging** | ✅ | ✅ | Configurable log levels |
| **Process Security** | ✅ | ✅ | Memory locking, ptrace protection |
| **Feature Flags** | ✅ | ✅ | Server-side feature detection |

### Format String Codes

All 14 format codes from C implementation:

| Code | Description | Example |
|------|-------------|---------|
| `%ai` | Account ID | `123456789` |
| `%an` | Account name (short) | `GitHub` |
| `%aN` | Account fullname with path | `Work/Dev/GitHub` |
| `%au` | Username | `user@example.com` |
| `%ap` | Password | `****` |
| `%am` | Modified time (UTC) | `2025-11-20 10:30:00` |
| `%aU` | Last touch time (local) | `Wed Nov 20 10:30:00` |
| `%as` | Share name | `TeamFolder` |
| `%ag` | Group name | `Work/Dev` |
| `%al` | URL | `https://github.com` |
| `%fn` | Field name | `Security Question` |
| `%fv` | Field value | `Answer` |
| `%/` | Conditional trailing slash | `/` or empty |
| `%%` | Literal percent | `%` |

## Python Advantages

The Python implementation provides **additional benefits** beyond the C CLI:

### 1. Python Library API

**Not available in C implementation:**

```python
# Import and use as a Python library
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "password")

# Direct access to vault data
accounts = client.get_accounts()
for account in accounts:
    if "important" in account.group.lower():
        print(f"{account.name}: {account.username}")
```

### 2. Type Hints & IDE Support

```python
from lastpass import LastPassClient, Account
from typing import List

def find_expired_passwords(client: LastPassClient) -> List[Account]:
    """Find all accounts - IDE autocomplete works!"""
    accounts: List[Account] = client.get_accounts()
    return [a for a in accounts if needs_update(a)]
```

### 3. Pythonic Exception Handling

```python
from lastpass.exceptions import (
    LoginFailedException,
    AccountNotFoundException
)

try:
    client.login("user@example.com", "password")
except LoginFailedException as e:
    print(f"Login failed: {e}")
```

### 4. Rich Data Models

```python
# Work with structured objects
account = client.find_account("github")

print(account.name)        # Type: str
print(account.username)    # Type: str
print(account.password)    # Type: str
print(account.url)         # Type: str

# Access custom fields
for field in account.fields:
    print(f"{field.name}: {field.value}")

# Convert to dict/JSON
data = account.to_dict()
```

### 5. Better Cross-Platform Support

| Platform | C CLI | Python CLI | Winner |
|----------|-------|------------|--------|
| Linux | ✅ Native | ✅ Native | Tie |
| macOS | ✅ Native | ✅ Native | Tie |
| Windows | ⚠️ Cygwin only | ✅ Native | **Python** |
| BSD | ✅ Native | ✅ Native | Tie |
| Termux/Android | ❌ Not supported | ✅ Works | **Python** |

### 6. No Compilation Required

- **C CLI:** Requires C compiler, make, libraries
- **Python CLI:** `pip install lastpass-py` - done!

## CLI Reference

### Common Commands

#### Login

```bash
lpass login user@example.com
lpass login user@example.com --trust --otp 123456
lpass login user@example.com --plaintext-key --force
```

Options:
- `--trust` - Trust this device
- `--otp CODE` - One-time password for 2FA
- `--force` - Force new login
- `--plaintext-key` - Store decryption key in plaintext (⚠️ less secure)
- `--color=auto|never|always` - Color output control

#### Show Account

```bash
lpass show github
lpass show github --password
lpass show github --username --clip
lpass show github --format="%au: %ap"
lpass show github --json
```

Options:
- `--password, -p` - Show only password
- `--username, -u` - Show only username
- `--url` - Show only URL
- `--notes, -n` - Show only notes
- `--field NAME` - Show specific field
- `--id` - Show account ID
- `--name` - Show account name
- `--all` - Show all details
- `--json, -j` - Output as JSON
- `--clip, -c` - Copy to clipboard
- `--expand-multi, -x` - Expand multi-line fields
- `--attach=ID` - Download attachment
- `--basic-regexp, -G` - Regex search
- `--fixed-strings, -F` - Substring search
- `--quiet, -q` - Suppress output
- `--format=FORMAT` - Custom printf-style format
- `--sync=auto|now|no` - Sync control

#### List Accounts

```bash
lpass ls
lpass ls Work
lpass ls --long -u
lpass ls --format="%/ag%an - %au"
lpass ls --json
```

Options:
- `--long, -l` - Long listing format
- `-m` - Show modified time
- `-u` - Show username
- `--json, -j` - JSON output
- `--format=FORMAT` - Custom format
- `--sync=auto|now|no` - Sync control

#### Generate Password

```bash
lpass generate 20
lpass generate mysite 20 --username=user --url=https://example.com
lpass generate 20 --no-symbols --clip
```

Options:
- `NAME` - Optional account name (creates account)
- `LENGTH` - Password length
- `--no-symbols` - Exclude special characters
- `--clip, -c` - Copy to clipboard
- `--username=USER` - Set username (when creating)
- `--url=URL` - Set URL (when creating)

#### Add Account

```bash
lpass add GitHub --username user --password pass
lpass add GitHub --username user --generate=20
lpass add "My Note" --note-type=sshkey
echo "password123" | lpass add site --username=user --non-interactive
```

Options:
- `--username, -u` - Username
- `--password, -p` - Password
- `--url` - URL
- `--notes` - Notes
- `--group` - Group/folder
- `--field=NAME:VALUE` - Custom field
- `--note-type=TYPE` - Secure note type
- `--generate=LENGTH` - Generate password
- `--non-interactive` - Read from stdin
- `--app` - Application entry

#### Edit Account

```bash
lpass edit GitHub --password
lpass edit GitHub --username newuser --url https://github.com
echo "newpassword" | lpass edit GitHub --password --non-interactive
```

Options:
- `--name` - Update name
- `--username, -u` - Update username
- `--password, -p` - Update password
- `--url` - Update URL
- `--notes` - Update notes
- `--group` - Move to group
- `--field=NAME:VALUE` - Update field
- `--non-interactive` - Read from stdin

#### Share Management

```bash
# Create shared folder
lpass share create "Team Passwords"

# Add user
lpass share useradd "Team Passwords" user@example.com --read-only

# List users
lpass share userls "Team Passwords"

# Remove user
lpass share userdel "Team Passwords" user@example.com

# Set access limits (allow list)
lpass share limit "Team Passwords" user@example.com acct1 acct2 --allow

# Set access limits (deny list)
lpass share limit "Team Passwords" user@example.com acct3 --deny

# Show limits
lpass share limit "Team Passwords" user@example.com --show
```

#### Other Commands

```bash
# Logout
lpass logout

# Status
lpass status

# Sync
lpass sync

# Remove
lpass rm github

# Move
lpass mv github Work/Development

# Duplicate
lpass duplicate github --name "GitHub Backup"

# Export
lpass export > vault.csv
lpass export --fields=url,username,password

# Import
lpass import vault.csv
```

## Python API Reference

### LastPassClient

```python
from lastpass import LastPassClient

client = LastPassClient(server="lastpass.com", config_dir=None)
```

### Authentication

```python
# Login
client.login(username, password=None, trust=False, otp=None, force=False)

# Logout
client.logout(force=False)

# Check login status
is_logged_in = client.is_logged_in()
```

### Vault Operations

```python
# Get all accounts
accounts = client.get_accounts(sync=True)

# Find account by name/ID/URL
account = client.find_account(query, sync=True)

# Search accounts
matches = client.search_accounts(query, sync=True, group=None)

# Advanced search
regex_matches = client.search_accounts_regex(pattern, sync=True)
substring_matches = client.search_accounts_fixed(text, sync=True)

# Sync vault
client.sync(force=False)

# Generate password
password = client.generate_password(length=16, symbols=True)
```

### Write Operations

```python
# Add account
account_id = client.add_account(
    name, username="", password="", url="",
    notes="", group="", fields=None, is_app=False
)

# Update account
client.update_account(
    query, name=None, username=None, password=None,
    url=None, notes=None, group=None, fields=None
)

# Delete account
client.delete_account(query)

# Duplicate account
new_id = client.duplicate_account(query, new_name=None)

# Move account
client.move_account(query, new_group)
```

### Attachments

```python
# Download attachment
data = client.get_attachment(query, attachment_id)

# Upload attachment
client.upload_attachment(query, filename, file_data)
```

### Share Management

```python
# Create shared folder
share_id = client.create_share(share_name)

# Delete shared folder
client.delete_share(share_name_or_id)

# List users
users = client.list_share_users(share_name_or_id)

# Add user
client.add_share_user(
    share_name_or_id, username,
    readonly=False, admin=False, hide_passwords=False
)

# Remove user
client.remove_share_user(share_name_or_id, username)

# Update permissions
client.update_share_user(
    share_name_or_id, username,
    readonly=None, admin=None, hide_passwords=None
)

# Set access limits
from lastpass.models import ShareLimit
limit = ShareLimit(whitelist=True, account_ids=['id1', 'id2'])
client.set_share_limits(share_name, username, limit)

# Get access limits
limit = client.get_share_limits(share_name, username)
```

### Import/Export

```python
# Export to CSV
csv_data = client.export_to_csv(fields=None, output=None)

# Import from CSV
count = client.import_from_csv(csv_data, keep_duplicates=False)
```

### Secure Notes

```python
from lastpass.note_types import NoteType

# Add secure note
note_id = client.add_secure_note(
    name="My SSH Key",
    note_type=NoteType.SSH_KEY,
    fields={
        "Hostname": "server.example.com",
        "Private Key": "-----BEGIN RSA PRIVATE KEY-----..."
    },
    group=""
)
```

### Data Models

```python
from lastpass.models import Account, Field, Attachment, Share

# Account object
account.id          # str
account.name        # str
account.username    # str
account.password    # str
account.url         # str
account.notes       # str
account.group       # str
account.fullname    # str
account.fields      # List[Field]
account.attachments # List[Attachment]
account.share       # Optional[Share]

# Methods
account.to_dict()              # Convert to dictionary
account.get_field(name)        # Get field by name

# Field object
field.name   # str
field.value  # str
field.type   # str

# Attachment object
attachment.id        # str
attachment.filename  # str
attachment.mimetype  # str

# Share object
share.id    # str
share.name  # str
```

### Exceptions

```python
from lastpass.exceptions import (
    LastPassException,           # Base exception
    LoginFailedException,        # Authentication failed
    InvalidSessionException,     # Session expired
    NetworkException,            # Network/HTTP error
    DecryptionException,         # Decryption failed
    AccountNotFoundException,    # Account not found
    InvalidPasswordException     # Invalid password
)

try:
    client.login("user@example.com", "wrong_password")
except LoginFailedException as e:
    print(f"Login failed: {e}")
```

## Examples

### CLI Usage

#### Custom Format Strings

```bash
# Full path with slashes
lpass ls --format="%/as%/ag%an"

# Credentials with labels
lpass show --format="Username: %au%nPassword: %ap%nURL: %al" github

# Formatted list with timestamps
lpass ls --format="[%am] %aN - %au"

# Export custom format
lpass ls --format="%aN,%au,%al" > accounts.csv
```

#### Advanced Search

```bash
# Regex search for production accounts
lpass show --basic-regexp "^prod.*"

# Substring search
lpass show --fixed-strings "example"

# Combined with formatting
lpass show --basic-regexp "github" --format="%au: %ap"
```

#### Clipboard Workflow

```bash
# Copy password to clipboard (auto-clears in 45s)
lpass show github --password --clip

# Generate and copy new password
lpass generate newsite 20 --clip

# Custom clipboard timeout
export LPASS_CLIP_CLEAR_TIME=60
lpass show github --password --clip
```

### Python API Usage

#### Password Rotation Script

```python
from lastpass import LastPassClient

client = LastPassClient()
client.login("user@example.com", "master_password")

# Rotate passwords for critical accounts
critical_accounts = ["github", "aws", "database"]

for account_name in critical_accounts:
    # Generate new password
    new_password = client.generate_password(length=32, symbols=True)
    
    # Update account
    client.update_account(account_name, password=new_password)
    print(f"Updated password for {account_name}")

client.sync(force=True)
```

#### Vault Analysis

```python
from lastpass import LastPassClient
import pandas as pd

client = LastPassClient()
client.login("user@example.com", "password")

# Export vault to DataFrame
accounts = client.get_accounts()
df = pd.DataFrame([a.to_dict() for a in accounts])

# Analyze
print(f"Total accounts: {len(df)}")
print(f"\nTop 10 sites:")
print(df['url'].value_counts().head(10))
print(f"\nAccounts by folder:")
print(df['group'].value_counts())
```

#### Backup and Restore

```python
from lastpass import LastPassClient
import json
from datetime import datetime

# Backup
client = LastPassClient()
client.login("user@example.com", "password")

accounts = client.get_accounts()
backup = {
    'timestamp': datetime.now().isoformat(),
    'accounts': [a.to_dict() for a in accounts]
}

with open(f'lastpass_backup_{datetime.now():%Y%m%d}.json', 'w') as f:
    json.dump(backup, f, indent=2)

# Restore (from CSV)
with open('backup.csv', 'r') as f:
    csv_data = f.read()
    
count = client.import_from_csv(csv_data)
print(f"Restored {count} accounts")
```

#### Integration Example

```python
from lastpass import LastPassClient
import paramiko

# Get SSH credentials from LastPass
client = LastPassClient()
client.login("user@example.com", "password")

server_account = client.find_account("production-server")

# Use credentials with SSH
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(
    hostname=server_account.url.replace('ssh://', ''),
    username=server_account.username,
    password=server_account.password
)

# Execute commands
stdin, stdout, stderr = ssh.exec_command('uptime')
print(stdout.read().decode())
```

## Environment Variables

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LPASS_HOME` | `~/.config/lpass` | Config directory location |
| `XDG_CONFIG_HOME` | `~/.config` | XDG config directory |
| `XDG_RUNTIME_DIR` | System default | Runtime directory |

### Agent System

| Variable | Default | Description |
|----------|---------|-------------|
| `LPASS_AGENT_TIMEOUT` | `3600` | Agent timeout in seconds (0=never) |
| `LPASS_AGENT_DISABLE` | Not set | Set to "1" to disable agent |

### Clipboard

| Variable | Default | Description |
|----------|---------|-------------|
| `LPASS_CLIPBOARD_COMMAND` | Auto-detect | Custom clipboard command |
| `LPASS_CLIP_CLEAR_TIME` | `45` | Clipboard clear timeout (seconds) |

### Password Input

| Variable | Default | Description |
|----------|---------|-------------|
| `LPASS_ASKPASS` | Not set | Custom askpass program |
| `LPASS_PINENTRY` | `pinentry` | Pinentry binary path |
| `LPASS_DISABLE_PINENTRY` | Not set | Set to "1" to disable GUI prompts |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LPASS_LOG_LEVEL` | `ERROR` | Log level (DEBUG/VERBOSE/INFO/WARNING/ERROR) |

### Editor

| Variable | Default | Description |
|----------|---------|-------------|
| `VISUAL` | Not set | Preferred editor |
| `EDITOR` | `vi` | Fallback editor |
| `SECURE_TMPDIR` | Not set | Secure temp directory |
| `TMPDIR` | `/tmp` | Standard temp directory |

### Display

| Variable | Default | Description |
|----------|---------|-------------|
| `NO_COLOR` | Not set | Disable color output |
| `BROWSER` | System default | Browser command for URLs |

## Testing

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# With coverage
pytest --cov=lastpass --cov-report=term-missing

# Verbose output
pytest -v

# Run specific test file
pytest tests/test_cli.py
```

### Test Statistics

- **481+ tests** passing
- **95% code coverage** overall
- Comprehensive unit and integration tests
- Mock-based testing for external services

## Contributing

We welcome contributions!

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/lastpass-py.git
cd lastpass-py

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check coverage
pytest --cov=lastpass --cov-report=term-missing
```

### Guidelines

- Follow PEP 8 style guidelines
- Add type hints to new functions
- Write tests for new features
- Maintain 95% coverage
- Update documentation

## Security

### Cryptography

- **Master Password:** Never stored or logged
- **Encryption:** AES-256-CBC with unique IVs
- **Key Derivation:** PBKDF2-HMAC-SHA256 (100,100+ iterations)
- **Session Storage:** Encrypted with derived key, mode 0600
- **Transport:** HTTPS with certificate verification
- **Memory Protection:** Secure clearing, memory locking (Unix)

### Security Features

- **Agent System:** Keys cached in memory only, Unix socket with credential verification
- **Upload Queue:** Encrypted queue entries on disk
- **Process Security:** Memory locking, ptrace protection, secure strings
- **Pinentry:** Secure password input with GUI isolation

### Reporting Security Issues

Please report security vulnerabilities to the maintainers privately.

## License

This project is licensed under the **GNU General Public License v2.0 or later (GPLv2+)**, the same license as the original LastPass CLI.

See [LICENSE](LICENSE) for full details.

## Acknowledgments

- Original [LastPass CLI](https://github.com/lastpass/lastpass-cli) by LastPass
- Python implementation by the community

## Disclaimer

This is an **independent implementation** and is not officially supported by LastPass/LogMeIn. Use at your own risk.

---

**Made with ❤️ by the community**
