# Installation Guide

This guide covers how to install lastpass-py.

## Table of Contents

- [Requirements](#requirements)
- [Installation Methods](#installation-methods)
  - [From PyPI (Recommended)](#from-pypi-recommended)
  - [From Source](#from-source)
  - [Development Installation](#development-installation)
- [Verification](#verification)
- [Optional Features](#optional-features)
- [Troubleshooting](#troubleshooting)

## Requirements

- **Python**: 3.8 or higher
- **pip**: Latest version recommended
- **Dependencies**: 
  - `requests >= 2.28.0`
  - `pycryptodome >= 3.15.0`

## Installation Methods

### From PyPI (Recommended)

The easiest way to install the library is from PyPI using pip:

```bash
pip install lastpass-py
```

To upgrade to the latest version:

```bash
pip install --upgrade lastpass-py
```

To install a specific version:

```bash
pip install lastpass-py==0.1.0
```

### From Source

To install directly from the GitHub repository:

```bash
# Clone the repository
git clone https://github.com/dynacylabs/lastpass-py.git
cd lastpass-py

# Install
pip install .
```

Or install directly from GitHub without cloning:

```bash
pip install git+https://github.com/dynacylabs/lastpass-py.git
```

### Development Installation

For development, install in editable mode with all dependencies:

```bash
# Clone the repository
git clone https://github.com/dynacylabs/lastpass-py.git
cd lastpass-py

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

This allows you to make changes to the code and see them reflected immediately without reinstalling.

## Optional Features

### Clipboard Support

For clipboard functionality with the `--clip` option:

```bash
pip install lastpass-py[clipboard]
```

This installs `pyperclip` for cross-platform clipboard support.

### Development Tools

If you need development tools:

```bash
pip install -r requirements.txt
```

This includes:
- pytest and plugins for testing
- black for code formatting
- ruff for linting
- mypy for type checking
- coverage tools
- responses for HTTP mocking

## Verification

After installation, verify it's working correctly:

### Command Line Verification

Test the CLI:

```bash
lpass --version
```

Test the Python module:

```bash
python -c "import lastpass; print('LastPass module imported successfully!')"
```

### Python Script Verification

Create a file `test_install.py`:

```python
from lastpass import LastPassClient

# Test basic functionality
client = LastPassClient()
print(f"✓ LastPass client created successfully!")
print(f"✓ Logged in: {client.is_logged_in()}")

# Test password generation
password = client.generate_password(length=20)
print(f"✓ Generated password: {password[:4]}...")
```

Run it:

```bash
python test_install.py
```

### Run Tests

If you installed from source:

```bash
# Run the test suite
./run_tests.sh unit

# Or use pytest directly
pytest tests/ -m unit -v
```

## Troubleshooting

### Common Issues

#### Import Error: No module named 'lastpass'

**Solution**: Make sure you've installed the package:
```bash
pip install lastpass-py
# or for development:
pip install -e .
```

#### Permission Denied Error

**Solution**: Use `--user` flag or a virtual environment:
```bash
pip install --user lastpass-py
```

Or create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install lastpass-py
```

#### Cryptography Errors

If you see errors about `pycryptodome`:

**Solution**: Ensure you have development headers installed:

On Ubuntu/Debian:
```bash
sudo apt-get install python3-dev libssl-dev
pip install --upgrade pycryptodome
```

On macOS:
```bash
brew install openssl
pip install --upgrade pycryptodome
```

On Windows:
```bash
# Usually works automatically with pip
pip install --upgrade pycryptodome
```

#### Old Version Installed

**Solution**: Force reinstall:
```bash
pip install --upgrade --force-reinstall lastpass-py
```

#### Dependency Conflicts

**Solution**: Use a fresh virtual environment:
```bash
python -m venv fresh_env
source fresh_env/bin/activate
pip install lastpass-py
```

#### CLI Command Not Found

After installation, if `lpass` command is not found:

**Solution**: Ensure pip's script directory is in your PATH:

On Linux/macOS:
```bash
export PATH="$HOME/.local/bin:$PATH"
# Add to ~/.bashrc or ~/.zshrc to make permanent
```

On Windows:
```bash
# Usually added automatically, but check:
# C:\Users\<username>\AppData\Local\Programs\Python\Python3x\Scripts
```

### Getting Help

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/dynacylabs/lastpass-py/issues) for similar problems
2. Search the [Discussions](https://github.com/dynacylabs/lastpass-py/discussions)
3. Create a new issue with:
   - Your Python version (`python --version`)
   - Your pip version (`pip --version`)
   - Your operating system
   - The full error message
   - Steps to reproduce the issue

## Next Steps

- Read the [Usage Guide](USAGE.md) to learn how to use the library
- Check the [Development Guide](DEVELOPMENT.md) for contributing
- Review the [API documentation](USAGE.md#api-reference)
- Compare with [C lastpass-cli](https://github.com/lastpass/lastpass-cli) for feature parity
