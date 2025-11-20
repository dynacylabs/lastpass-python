# Development Guide

This guide covers the development workflow, testing, and release process for lastpass-py.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Code Coverage](#code-coverage)
- [Development Workflow](#development-workflow)
- [Release Process](#release-process)
- [Continuous Integration](#continuous-integration)
- [Debugging](#debugging)
- [Performance](#performance)

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- pip
- Virtual environment tool (venv, virtualenv, or conda)
- LastPass account (optional, for live testing)

### Initial Setup

1. **Clone the Repository**

```bash
git clone https://github.com/dynacylabs/lastpass-py.git
cd lastpass-py
```

2. **Create Virtual Environment**

```bash
# Using venv (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using conda
conda create -n lastpass-py python=3.11
conda activate lastpass-py
```

3. **Install Development Dependencies**

```bash
# Install package in editable mode
pip install -e .

# Install all development dependencies
pip install -r requirements.txt
```

4. **Verify Installation**

```bash
# Run tests
./run_tests.sh unit

# Check CLI
lpass --version

# Check imports
python -c "from lastpass import LastPassClient; print('Success!')"
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer
- Coverage Gutters
- GitLens

Recommended settings (`.vscode/settings.json`):

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.analysis.typeCheckingMode": "basic",
    "editor.formatOnSave": true,
    "editor.rulers": [100]
}
```

#### PyCharm

1. Mark `lastpass/` as Sources Root
2. Enable pytest as test runner
3. Configure Python 3.8+ interpreter
4. Enable type checking
5. Set Black as code formatter

## Project Structure

```
lastpass-py/
├── lastpass/               # Main package
│   ├── __init__.py        # Package exports
│   ├── agent.py           # SSH agent integration
│   ├── blob.py            # Vault blob parsing
│   ├── browser.py         # Browser integration
│   ├── cipher.py          # Encryption/decryption
│   ├── cli.py             # Command-line interface
│   ├── client.py          # Main API client
│   ├── clipboard.py       # Clipboard operations
│   ├── config.py          # Configuration management
│   ├── csv_utils.py       # CSV import/export
│   ├── editor.py          # Text editor integration
│   ├── exceptions.py      # Custom exceptions
│   ├── feature_flag.py    # Feature flag support
│   ├── format.py          # Output formatting
│   ├── http.py            # HTTP client
│   ├── kdf.py             # Key derivation functions
│   ├── logger.py          # Logging utilities
│   ├── models.py          # Data models
│   ├── note_types.py      # Secure note templates
│   ├── notes.py           # Note handling
│   ├── pinentry.py        # PIN entry dialog
│   ├── process_security.py # Process security
│   ├── session.py         # Session management
│   ├── terminal.py        # Terminal utilities
│   ├── upload_queue.py    # Upload queue management
│   └── xml_parser.py      # XML response parsing
│
├── tests/                  # Test suite
│   ├── conftest.py        # Shared fixtures
│   ├── test_*.py          # Test modules (25+ files)
│   └── __pycache__/
│
├── lastpass-cli/           # Reference C implementation
│
├── .github/                # GitHub configuration
│   └── workflows/         # CI/CD workflows
│       ├── tests.yml      # Test automation
│       ├── publish-to-pypi.yml  # PyPI publishing
│       ├── security.yml   # Security scanning
│       └── dependency-updates.yml # Dependency checks
│
├── docs/                   # Documentation
├── .gitignore             # Git ignore patterns
├── LICENSE                # GPL-2.0 License
├── LICENSE.OpenSSL        # OpenSSL exception
├── MANIFEST.in            # Package manifest
├── README.md              # Main documentation
├── INSTALL.md             # Installation guide
├── USAGE.md               # Usage guide
├── CONTRIBUTING.md        # Contribution guidelines
├── DEVELOPMENT.md         # This file
├── FEATURE_PARITY_ANALYSIS.md # CLI parity tracking
├── pyproject.toml         # Project metadata
├── setup.py               # Setup script
├── pytest.ini             # Pytest configuration
├── requirements.txt       # Development dependencies
└── run_tests.sh           # Test runner script
```

## Testing

### Running Tests

Use the provided test runner script:

```bash
# Run all tests (excluding live API tests)
./run_tests.sh

# Run only unit tests (fast, mocked)
./run_tests.sh unit

# Run integration tests
./run_tests.sh integration

# Run with coverage report
./run_tests.sh coverage

# Run specific test file
./run_tests.sh tests/test_client.py

# Run specific test
./run_tests.sh tests/test_client.py::TestLastPassClient::test_login
```

Or use pytest directly:

```bash
# All tests (excluding live)
pytest -m "not live"

# Verbose output
pytest -v -m "not live"

# Stop on first failure
pytest -x -m "not live"

# Run tests matching pattern
pytest -k "test_login" -m "not live"

# Run tests with marker
pytest -m unit
pytest -m integration
pytest -m slow
```

### Live API Testing

**Warning**: Live tests modify your LastPass vault. Use a test account!

```bash
# Set credentials (use a test account!)
export LASTPASS_USERNAME="test@example.com"
export LASTPASS_PASSWORD="testpassword"

# Run live tests
pytest -m live --username "$LASTPASS_USERNAME" --password "$LASTPASS_PASSWORD"
```

### Writing Tests

Follow these guidelines:

1. **Location**: Place tests in `tests/` directory
2. **Naming**: Name test files `test_*.py`
3. **Structure**: Group related tests in classes
4. **Markers**: Use pytest markers appropriately
5. **Fixtures**: Use fixtures from `conftest.py`
6. **Mocking**: Use `responses` library for HTTP mocking

Example test structure:

```python
import pytest
from lastpass import LastPassClient

@pytest.mark.unit
class TestLastPassClient:
    """Tests for the LastPassClient class."""
    
    def test_login_success(self, mock_http_responses):
        """Test successful login."""
        client = LastPassClient()
        session = client.login("user@example.com", "password")
        assert session is not None
        assert client.is_logged_in()
```

### Test Markers

Available markers (defined in `pytest.ini`):

- `@pytest.mark.unit`: Unit tests (fast, mocked)
- `@pytest.mark.integration`: Integration tests (may hit external services)
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.live`: Tests requiring live LastPass API connection

Usage:

```python
@pytest.mark.unit
def test_fast_operation():
    pass

@pytest.mark.live
@pytest.mark.slow
def test_live_api():
    pass
```

Run specific markers:

```bash
pytest -m unit           # Only unit tests
pytest -m "not slow"     # Exclude slow tests
pytest -m "not live"     # Exclude live API tests (default)
```

## Code Coverage

### Measuring Coverage

```bash
# Generate coverage report
./run_tests.sh coverage

# View in terminal
coverage report

# Generate HTML report
coverage html
# Open htmlcov/index.html in browser

# Generate XML report (for CI)
coverage xml
```

### Coverage Goals

- **Overall**: 95%+ coverage (current: 62%)
- **New Code**: 100% coverage
- **Critical Paths**: 100% coverage (login, encryption, blob parsing)

### Checking Coverage Locally

```bash
# Run tests with coverage
pytest --cov=lastpass --cov-report=term-missing -m "not live"

# Fail if coverage below threshold
pytest --cov=lastpass --cov-report=term --cov-fail-under=95 -m "not live"
```

## Development Workflow

### Daily Development

1. **Pull Latest Changes**

```bash
git checkout main
git pull origin main
```

2. **Create Feature Branch**

```bash
git checkout -b feature/new-feature
```

3. **Make Changes**

- Edit code
- Add tests
- Update docs

4. **Run Tests**

```bash
./run_tests.sh
```

5. **Format and Lint**

```bash
# Format with Black
black lastpass/ tests/

# Lint with Ruff
ruff check lastpass/ tests/

# Type check with MyPy
mypy lastpass/
```

6. **Commit Changes**

```bash
git add .
git commit -m "feat: Add new feature"
```

7. **Push and Create PR**

```bash
git push origin feature/new-feature
# Then create PR on GitHub
```

### Code Quality Tools

#### Black (Code Formatting)

```bash
# Format all code
black lastpass/ tests/

# Check formatting without changing
black --check lastpass/ tests/

# Format specific file
black lastpass/client.py
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311', 'py312']
```

#### Ruff (Linting)

```bash
# Lint all code
ruff check lastpass/ tests/

# Auto-fix issues
ruff check --fix lastpass/ tests/

# Lint specific file
ruff check lastpass/client.py
```

#### MyPy (Type Checking)

```bash
# Type check package
mypy lastpass/

# Strict mode
mypy --strict lastpass/

# Check specific file
mypy lastpass/client.py
```

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Creating a Release

1. **Update Version**

Version is managed by `setuptools_scm` based on git tags.

2. **Update CHANGELOG** (if exists)

Document changes in CHANGELOG.md.

3. **Create and Push Tag**

```bash
# Create annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push tag
git push origin v0.1.0
```

4. **Create GitHub Release**

- Go to GitHub Releases
- Click "Draft a new release"
- Select the tag
- Fill in release notes
- Publish release

5. **Automated Publishing**

GitHub Actions will automatically:
- Run tests
- Build distribution packages
- Publish to PyPI (if configured)

### Manual Publishing to PyPI

If needed, publish manually:

```bash
# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to TestPyPI (for testing)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Continuous Integration

### GitHub Actions Workflows

#### Tests Workflow (`.github/workflows/tests.yml`)

Runs on:
- Push to main
- Pull requests
- Daily schedule (2am UTC)

Actions:
- Test on Python 3.9, 3.10, 3.11, 3.12
- Run linting and type checking
- Generate coverage reports
- Upload to Codecov

#### Security Workflow (`.github/workflows/security.yml`)

Runs weekly and on pushes.

Scans:
- Dependency vulnerabilities (Safety)
- Code security issues (Bandit)
- Secret detection (TruffleHog)
- CodeQL analysis

#### Publish Workflow (`.github/workflows/publish-to-pypi.yml`)

Triggers on GitHub releases.

Actions:
- Build distribution packages
- Publish to PyPI using trusted publishing

### Local CI Simulation

Run the same checks locally:

```bash
# Run all tests like CI
pytest -v --cov=lastpass --cov-report=term-missing -m "not live"

# Run linting
black --check lastpass/ tests/
ruff check lastpass/ tests/
mypy lastpass/

# Security scan
pip install safety bandit
safety check
bandit -r lastpass/
```

## Debugging

### Using pdb

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Python 3.7+ breakpoint()
breakpoint()
```

### Using pytest debugger

```bash
# Drop into debugger on failure
pytest --pdb -m "not live"

# Drop into debugger on first failure
pytest -x --pdb -m "not live"
```

### Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
```

## Performance

### Profiling

```python
# Using cProfile
python -m cProfile -o profile.stats -m lastpass.cli show account

# Analyze profile
python -m pstats profile.stats
# Then: sort time, stats 10
```

### Memory Profiling

```bash
# Install memory_profiler
pip install memory_profiler

# Profile script
python -m memory_profiler script.py
```

### Benchmarking

```python
import timeit

# Time a function
time = timeit.timeit(
    'client.generate_password()',
    setup='from lastpass import LastPassClient; client = LastPassClient()',
    number=10000
)
print(f"Time: {time}")
```

## Troubleshooting

### Common Issues

**Import errors after changes**:
```bash
pip install -e .
```

**Tests not found**:
```bash
# Ensure tests directory has __init__.py
# Check pytest.ini configuration
pytest --collect-only
```

**Coverage not working**:
```bash
# Reinstall in editable mode
pip uninstall lastpass-py
pip install -e .
```

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [LastPass CLI (C implementation)](https://github.com/lastpass/lastpass-cli)

## Getting Help

- Check GitHub Issues
- Read documentation
- Ask in GitHub Discussions
- Contact maintainers
