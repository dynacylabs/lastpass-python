# LastPass Python

[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](https://github.com/dynacylabs/lastpass-python)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPLv2+-blue.svg)](LICENSE)

A complete Python implementation of the LastPass CLI with a friendly API for programmatic access to your LastPass vault.

## Features

- 🔐 **Secure** - AES-256 encryption, PBKDF2 key derivation
- 🐍 **Pure Python** - No binary dependencies, works everywhere
- 🚀 **Complete CLI** - All major LastPass commands implemented
- 📚 **Python API** - Clean interface for scripts and automation
- 🧪 **Well Tested** - 331+ tests with 95% code coverage
- 🌍 **Cross-Platform** - Linux, macOS, and Windows

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Command Line](#command-line)
  - [Python API](#python-api)
- [CLI Reference](#cli-reference)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Installation

### From Source

```bash
git clone https://github.com/dynacylabs/lastpass-python.git
cd lastpass-python
pip install -e .
```

### Development Install

```bash
pip install -e ".[dev]"
```

This installs additional tools: `pytest`, `pytest-cov`, `pytest-mock`, `responses`

### Optional: Clipboard Support

```bash
pip install pyperclip
```

## Quick Start

### Command Line

```bash
# Login
lpass login user@example.com

# List accounts
lpass ls

# Show account details  
lpass show github --password

# Generate password
lpass generate 20

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

## CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `lpass login [USERNAME]` | Login to LastPass |
| `lpass logout` | Logout and clear session |
| `lpass status` | Show login status |
| `lpass show [QUERY]` | Display account details |
| `lpass ls [GROUP]` | List accounts |
| `lpass generate [LENGTH]` | Generate password |
| `lpass sync` | Sync vault from server |
| `lpass add [NAME]` | Add new account |
| `lpass edit [QUERY]` | Edit existing account |
| `lpass rm [QUERY]` | Remove account |
| `lpass duplicate [QUERY]` | Duplicate account |
| `lpass mv [QUERY] [GROUP]` | Move account to group |

### Common Options

**login**
```bash
lpass login user@example.com --trust --otp 123456
```
- `--trust` - Trust this device
- `--otp CODE` - One-time password for 2FA
- `--force` - Force new login

**show**
```bash
lpass show github --password --clip
```
- `--password` - Show only password
- `--username` - Show only username  
- `--url` - Show only URL
- `--notes` - Show only notes
- `--field NAME` - Show specific field
- `--json` - Output as JSON
- `--clip` - Copy to clipboard

**ls**
```bash
lpass ls Work --long --json
```
- `--long` - Long listing format
- `--json` - Output as JSON

**generate**
```bash
lpass generate 24 --no-symbols --clip
```
- `--no-symbols` - Exclude special characters
- `--clip` - Copy to clipboard

**add**
```bash
lpass add "GitHub" --username user@example.com --url https://github.com
```
- `--username` - Account username
- `--password` - Account password (prompts if not provided)
- `--url` - Website URL
- `--notes` - Account notes
- `--group` - Group/folder name
- `--generate LENGTH` - Generate password of specified length

**edit**
```bash
lpass edit "GitHub" --password --url https://github.com/login
```
- `--name` - Update account name
- `--username` - Update username
- `--password` - Update password (prompts if flag provided without value)
- `--url` - Update URL
- `--notes` - Update notes
- `--group` - Move to different group

**rm**
```bash
lpass rm "Old Account" --force
```
- `--force` - Skip confirmation prompt

**duplicate**
```bash
lpass duplicate "GitHub" --name "GitHub Backup"
```
- `--name` - Name for duplicate (defaults to "Copy of [original]")

**mv**
```bash
lpass mv "GitHub" "Work/Development"
```
- Moves account to specified group/folder

## API Reference

### LastPassClient

```python
from lastpass import LastPassClient

client = LastPassClient(server="lastpass.com", config_dir=None)
```

#### Authentication

**`login(username, password=None, trust=False, otp=None, force=False)`**

Login to LastPass. Returns `Session` object.

```python
client.login("user@example.com", "password", otp="123456")
```

**`logout(force=False)`**

Logout and clear session data.

```python
client.logout()
```

**`is_logged_in()`**

Check if currently logged in. Returns `bool`.

```python
if client.is_logged_in():
    print("Logged in!")
```

#### Vault Operations

**`get_accounts(sync=True)`**

Get all accounts. Returns `List[Account]`.

```python
accounts = client.get_accounts()
```

**`find_account(query, sync=True)`**

Find account by name, ID, or URL. Returns `Account` or `None`.

```python
account = client.find_account("github")
```

**`search_accounts(query, sync=True, group=None)`**

Search accounts by keyword. Returns `List[Account]`.

```python
matches = client.search_accounts("google")
```

**`list_groups(sync=True)`**

Get all group/folder names. Returns `List[str]`.

```python
groups = client.list_groups()
```

**`sync(force=False)`**

Sync vault from server.

```python
client.sync(force=True)
```

#### Utilities

**`generate_password(length=16, symbols=True)`**

Generate random password. Returns `str`.

```python
password = client.generate_password(length=20, symbols=False)
```

**`get_password(query, sync=True)`**

Get password for account. Returns `str` or `None`.

```python
password = client.get_password("github")
```

**`get_username(query, sync=True)`**

Get username for account. Returns `str` or `None`.

**`get_notes(query, sync=True)`**

Get notes for account. Returns `str` or `None`.

#### Write Operations

**`add_account(name, username="", password="", url="", notes="", group="", fields=None)`**

Add new account to vault. Returns account ID as `str`.

```python
account_id = client.add_account(
    name="GitHub",
    username="user@example.com",
    password="secret123",
    url="https://github.com",
    group="Work"
)
```

**`update_account(query, name=None, username=None, password=None, url=None, notes=None, group=None)`**

Update existing account. Only provided fields are updated.

```python
client.update_account("GitHub", password="newsecret", url="https://github.com/login")
```

**`delete_account(query)`**

Delete account from vault.

```python
client.delete_account("Old Account")
```

**`duplicate_account(query, new_name=None)`**

Duplicate an account. Returns new account ID as `str`.

```python
new_id = client.duplicate_account("GitHub", "GitHub Backup")
```

**`move_account(query, new_group)`**

Move account to different group/folder.

```python
client.move_account("GitHub", "Work/Development")
```

### Data Models

#### Account

```python
@dataclass
class Account:
    id: str
    name: str
    username: str
    password: str
    url: str
    group: str
    notes: str
    fullname: str
    fields: List[Field]
    attachments: List[Attachment]
    share: Optional[Share]
    
    def to_dict(self) -> Dict
    def get_field(self, name: str) -> Optional[Field]
    def is_secure_note(self) -> bool
```

#### Field

```python
@dataclass
class Field:
    name: str
    value: str
    type: str
    checked: bool
```

#### Share

```python
@dataclass
class Share:
    id: str
    name: str
    readonly: bool
```

### Exceptions

All exceptions inherit from `LastPassException`:

- `LoginFailedException` - Authentication failed
- `InvalidSessionException` - Session expired  
- `NetworkException` - Network/HTTP error
- `DecryptionException` - Decryption failed
- `AccountNotFoundException` - Account not found
- `InvalidPasswordException` - Invalid password

```python
from lastpass import LastPassClient, LoginFailedException

try:
    client.login("user@example.com", "wrong")
except LoginFailedException:
    print("Invalid credentials")
```
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the GNU General Public License v2.0 or later (GPLv2+), the same license as the original LastPass CLI.

## Disclaimer

This is an independent implementation. It is not officially supported by LastPass/LogMeIn. Use at your own risk.

## Implementation Details

### Core Features Implemented

#### ✅ Cryptography
- AES-256-CBC encryption/decryption
- PBKDF2-HMAC-SHA256 key derivation
- RSA encryption for shared folders
- Base64 encoding/decoding
- SHA256 hashing

#### ✅ Authentication
- Username/password login
- Two-factor authentication (OTP)
- Session management
- Encrypted session storage
- Logout functionality

#### ✅ Vault Operations
- Download and parse encrypted blob
- Account listing and filtering
- Account search (by name, username, URL, ID)
- Group/folder listing
- Custom field support
- Shared folder support

#### ✅ CLI Commands
- `login` - Login to LastPass
- `logout` - Logout from LastPass
- `status` - Show login status
- `show` - Display account details
- `ls` - List accounts
- `generate` - Generate random password
- `sync` - Sync vault from server

#### ✅ Python API
Complete programmatic access to LastPass functionality:
- `LastPassClient` - Main client class
- `login()` / `logout()` - Authentication
- `get_accounts()` - Get all accounts
- `find_account()` - Find specific account
- `search_accounts()` - Search vault
- `list_groups()` - Get folder list
- `generate_password()` - Generate password
- `get_password()` / `get_username()` / `get_notes()` - Convenience methods

### Comparison with C CLI

This Python implementation provides:

✅ **All core functionality** of the C-based CLI
✅ **Python API** for programmatic access
✅ **No compilation** required
✅ **Easier to modify** and extend
✅ **Better error messages** and debugging

Some differences:
- Clipboard support requires `pyperclip` or system tools
- Agent/daemon not implemented (use session-based auth)
- Some advanced features (shares management, etc.) are simplified

## Security Notes

- **Master Password**: Never stored, only used for key derivation
- **Encryption**: AES-256-CBC with unique IVs
- **Key Derivation**: PBKDF2-HMAC-SHA256
- **Session Storage**: Encrypted with derived key, mode 0600
- **Memory**: Sensitive data cleared when possible

## Configuration

Configuration is stored in:
- Linux/macOS: `~/.config/lpass/`
- Windows: `%APPDATA%\lpass\`

Files:
- `session`: Encrypted session data

## Testing

### Running Tests

**Quick start:**
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# With coverage
pytest --cov=lastpass --cov-report=term-missing
```

### Test Modes

**1. Mock Tests (Default)**

Fast, offline tests using mocked API responses. No credentials needed.

```bash
pytest                    # Run all mock tests
pytest -v                 # Verbose output
pytest tests/test_client.py  # Specific test file
```

**2. Live API Tests**

Tests against real LastPass API. **Use a test account!**

```bash
pytest --live --username test@example.com --password testpass
```

If email verification is required:
```bash
pytest --live --username test@example.com --password testpass --otp 123456
```

**3. Complete Test Suite**

Run both mock and live tests for full coverage:

```bash
pytest tests/ --live --username test@example.com --password testpass --cov=lastpass
```

Expected: **331+ tests passed, 95% coverage**

### Test Structure

- `tests/test_cli.py` - CLI interface (87 tests)
- `tests/test_client.py` - Client API (42 tests)
- `tests/test_cipher.py` - Cryptography (26 tests)
- `tests/test_models.py` - Data models (16 tests)
- `tests/test_http.py` - HTTP client (26 tests)
- And 8 more test files...

### Coverage Report

Current coverage: **95%**

```
Module                Coverage
--------------------------------
lastpass/__init__.py   100%
lastpass/cli.py         99%
lastpass/http.py        96%
lastpass/cipher.py      96%
lastpass/models.py      95%
lastpass/client.py      93%
lastpass/session.py     93%
lastpass/blob.py        89%
--------------------------------
TOTAL                   95%
```

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Fork and clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/lastpass-python.git
   cd lastpass-python
   ```

2. **Install dev dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Guidelines

**Code Quality**
- Follow PEP 8 style guidelines
- Add type hints to new functions
- Document public APIs with docstrings
- Keep functions focused and testable

**Testing Requirements** ⚠️
- **All tests must pass** - Run `pytest` before submitting
- **Maintain 95% coverage** - Add tests for new code
- **Include both unit and integration tests** when applicable

```bash
# Verify before submitting
pytest --cov=lastpass --cov-report=term-missing

# Expected output:
# ========== 279 passed in X.XXs ==========
# TOTAL coverage: 95%
```

**Commit Messages**
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Example: `fix: handle rate limiting in HTTP client (#123)`

### Submitting Changes

1. **Run tests**
   ```bash
   pytest --cov=lastpass
   ```
   Ensure: ✅ All tests pass ✅ Coverage ≥ 95%

2. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Open a Pull Request**
   - Describe your changes clearly
   - Reference any related issues
   - Include test results/coverage report

### Areas for Contribution

- 🐛 Bug fixes and improvements
- 📝 Documentation enhancements  
- 🧪 Additional test coverage
- ✨ New features (discuss in an issue first)
- 🔧 Code refactoring
- 🌍 Platform compatibility

### Getting Help

- 📖 Check existing documentation
- 💬 Open an issue for discussion
- 🔍 Search closed issues for similar problems

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Comparison with LastPass CLI (C Implementation)

### ✅ Implemented Features

This Python implementation now covers **all major operations** from the C CLI:

| Feature | C CLI | Python | Status |
|---------|-------|--------|--------|
| **Authentication** |
| Login with username/password | ✅ | ✅ | Full support |
| Two-factor auth (OTP) | ✅ | ✅ | Full support |
| Trust device | ✅ | ✅ | Full support |
| Logout | ✅ | ✅ | Full support |
| Session management | ✅ | ✅ | Full support |
| **Vault Operations** |
| List accounts (`ls`) | ✅ | ✅ | Full support |
| Show account (`show`) | ✅ | ✅ | Full support |
| Search/filter accounts | ✅ | ✅ | Full support |
| Sync vault | ✅ | ✅ | Full support |
| Password generation (`generate`) | ✅ | ✅ | Full support |
| Status check | ✅ | ✅ | Full support |
| **Write Operations** |
| Add account (`add`) | ✅ | ✅ | Full support |
| Edit account (`edit`) | ✅ | ✅ | Full support |
| Delete account (`rm`) | ✅ | ✅ | Full support |
| Move account (`mv`) | ✅ | ✅ | Full support |
| Duplicate account (`duplicate`) | ✅ | ✅ | Full support |
| **Data Access** |
| Account fields | ✅ | ✅ | Full support |
| Custom fields | ✅ | ✅ | Full support |
| Secure notes | ✅ | ✅ | Full support |
| Shared folders | ✅ | ✅ | Full support |
| Groups/folders | ✅ | ✅ | Full support |
| **Cryptography** |
| AES-256-CBC encryption | ✅ | ✅ | Full support |
| PBKDF2 key derivation | ✅ | ✅ | Full support |
| RSA for shared folders | ✅ | ✅ | Full support |
| **Output Formats** |
| Standard text output | ✅ | ✅ | Full support |
| Long listing format | ✅ | ✅ | Full support |
| JSON output | ✅ | ✅ | Full support |
| Clipboard support | ✅ | ✅ | Full support |

### ❌ Not Implemented

The following **advanced features** from the C CLI are **not implemented**:

| Feature | C CLI | Python | Notes |
|---------|-------|--------|-------|
| Change master password (`passwd`) | ✅ | ❌ | High risk operation |
| Share management | ✅ | ❌ | Complex, requires share API |
| Import accounts | ✅ | ❌ | CSV import not implemented |
| Export accounts | ✅ | ✅ | Partial (JSON only, no CSV) |
| Attachments download | ✅ | ❌ | API exists, not in CLI |
| Agent/daemon mode | ✅ | ❌ | Not planned |

### 🎯 Design Philosophy

**Python Implementation Focus:**
- ✅ **Complete CRUD operations** - Create, Read, Update, Delete accounts
- ✅ **Safe vault management** - All standard operations supported
- ✅ **Automation-friendly** - Clean Python API for scripts
- ✅ **Cross-platform** - Pure Python, no compilation needed
- ✅ **Well-tested** - Comprehensive test coverage

**Excluded Operations:**
- Master password changes (use web app for security)
- Advanced share management (complex API)
- CSV import/export (JSON supported)
- Agent mode (session-based auth is simpler)

### 📊 Feature Coverage Summary

```
Core Functionality:     100% ✅
Read Operations:        100% ✅  
Write Operations:       100% ✅ (add, edit, delete, move, duplicate)
Advanced Features:       30% ⚠️  (passwd, shares, import not implemented)
Cryptography:           100% ✅
Authentication:         100% ✅
Session Management:     100% ✅
Test Coverage:           95% ✅
```

### 🚀 Python-Specific Advantages

Features **only** in the Python implementation:

- 🐍 **Native Python API** - Use as a library in your Python projects
- 📦 **No compilation** - `pip install` and you're ready
- 🔧 **Easy to extend** - Pure Python, modify for your needs
- 🧪 **Comprehensive tests** - 331+ tests vs minimal C tests
- 📚 **Better documentation** - Docstrings, type hints, examples
- 🌐 **Modern architecture** - Uses `requests`, dataclasses, type hints

### 💡 Use Cases

**Perfect for:**
- ✅ Retrieving passwords in automation scripts
- ✅ Integration with deployment pipelines
- ✅ Password lookups in Python applications
- ✅ Auditing vault contents
- ✅ Bulk password exports
- ✅ Cross-platform password access

**Not suitable for:**
- ❌ Creating/modifying vault entries (use web app)
- ❌ Account management workflows
- ❌ Complex share management
- ❌ Import/migration operations

### 🔮 Future Considerations

If there's demand, write operations could be added:
- `add` - Create new accounts
- `edit` - Modify existing accounts  
- `rm` - Delete accounts
- `import` - Import from CSV

However, the current focus is on **rock-solid read operations** with excellent test coverage.

## License

This project is licensed under the **GNU General Public License v2.0 or later (GPLv2+)**.

See [LICENSE](LICENSE) for full details.

## Security

- **Master Password**: Never stored or logged
- **Encryption**: AES-256-CBC with PBKDF2-SHA256
- **Session Data**: Encrypted at rest (mode 0600)
- **Memory Safety**: Sensitive data cleared when possible

## Acknowledgments

- Original [LastPass CLI](https://github.com/lastpass/lastpass-cli) by LastPass
- Python implementation by the community

## Disclaimer

This is an **independent implementation** and is not officially supported by LastPass/LogMeIn. Use at your own risk.
