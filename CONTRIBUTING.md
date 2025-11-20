# Contributing to lastpass-py

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Quality Standards](#code-quality-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of background or experience level.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Be patient with questions and discussions
- Respect differing viewpoints and experiences

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Trolling, insulting, or derogatory comments
- Publishing others' private information
- Any conduct inappropriate for a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.8 or higher installed
- Git installed and configured
- A GitHub account
- Familiarity with pytest for testing
- A LastPass account (for testing, optional)

### First-Time Contributors

If this is your first contribution:

1. **Find an Issue**: Look for issues labeled `good first issue` or `help wanted`
2. **Ask Questions**: Don't hesitate to ask for clarification in the issue comments
3. **Small Changes**: Start with small, manageable changes
4. **Read the Docs**: Familiarize yourself with the [Usage Guide](USAGE.md) and [Development Guide](DEVELOPMENT.md)

## Development Setup

See the [Development Guide](DEVELOPMENT.md) for detailed setup instructions.

Quick setup:

```bash
# Clone the repository
git clone https://github.com/dynacylabs/lastpass-py.git
cd lastpass-py

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install -r requirements.txt

# Run tests to verify setup
./run_tests.sh unit
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Fixes**: Fix issues reported in the issue tracker
- **New Features**: Add new functionality (sync with maintainers first)
- **Documentation**: Improve docs, add examples, fix typos
- **Tests**: Add test coverage, improve test quality
- **Performance**: Optimize code for better performance
- **Refactoring**: Improve code structure and readability

### Reporting Bugs

When reporting bugs, include:

- **Clear Title**: Descriptive summary of the issue
- **Description**: Detailed explanation of the problem
- **Steps to Reproduce**: Exact steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: Python version, OS, package version
- **Code Sample**: Minimal code to reproduce the issue

Example bug report:

```markdown
**Title**: Client.login() fails with MFA enabled

**Description**: When trying to login with a LastPass account that has MFA enabled, the client raises an unexpected error.

**Steps to Reproduce**:
1. Create a client: `client = LastPassClient()`
2. Login with MFA account: `client.login("user@example.com", "password")`
3. Error occurs

**Expected**: Should prompt for OTP code
**Actual**: Raises AttributeError

**Environment**: Python 3.11, Ubuntu 22.04, lastpass-py version 0.1.0

**Code Sample**:
\```python
from lastpass import LastPassClient
client = LastPassClient()
client.login("user@example.com", "password")
\```
```

### Suggesting Features

When suggesting new features:

1. **Check Existing Issues**: Search for similar feature requests
2. **Describe the Feature**: Clearly explain what you want
3. **Use Cases**: Provide real-world use cases
4. **CLI Parity**: Mention if the feature exists in the C lastpass-cli
5. **Implementation Ideas**: Optional but helpful

### Making Changes

1. **Fork the Repository**

```bash
# Fork via GitHub UI, then clone
git clone https://github.com/YOUR-USERNAME/lastpass-py.git
cd lastpass-py
```

2. **Create a Branch**

```bash
# Create a descriptive branch name
git checkout -b feature/add-attachment-support
# or
git checkout -b fix/mfa-login-error
```

3. **Make Your Changes**

- Write clean, readable code
- Follow the style guide
- Add or update tests
- Update documentation

4. **Test Your Changes**

```bash
# Run all tests
./run_tests.sh

# Run specific tests
pytest tests/test_client.py -v

# Check coverage
./run_tests.sh coverage
```

5. **Commit Your Changes**

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add attachment upload support"
```

Follow commit message conventions:
- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Fix bug" not "Fixes bug"
- Keep first line under 50 characters
- Reference issues: "Fix MFA login error (#123)"

6. **Push to Your Fork**

```bash
git push origin feature/add-attachment-support
```

7. **Open a Pull Request**

- Go to your fork on GitHub
- Click "Pull Request"
- Fill in the PR template
- Link related issues

## Code Quality Standards

### Code Style

We use several tools to maintain code quality:

```bash
# Format code with Black
black lastpass/ tests/

# Lint with Ruff
ruff check lastpass/ tests/

# Type check with MyPy
mypy lastpass/
```

### Code Review Checklist

Before submitting, ensure:

- [ ] Code follows Python conventions (PEP 8)
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] No linting errors
- [ ] Type hints are used where appropriate
- [ ] Docstrings are added for public APIs
- [ ] Changes are backward compatible (or migration guide provided)
- [ ] Coverage is maintained at 95%+

## Testing Requirements

### Writing Tests

- All new features must include tests
- Bug fixes should include regression tests
- Tests should be clear and well-documented
- Use descriptive test names
- Use appropriate markers (@pytest.mark.unit, @pytest.mark.integration)

Example test:

```python
import pytest
from lastpass import LastPassClient

@pytest.mark.unit
class TestLastPassClient:
    """Test the LastPassClient class."""
    
    def test_login_with_valid_credentials(self, mock_http_client):
        """Test that login works with valid credentials."""
        client = LastPassClient()
        session = client.login("user@example.com", "password")
        assert session is not None
        assert client.is_logged_in()
```

### Running Tests

```bash
# All tests
./run_tests.sh

# Unit tests only (fast, mocked)
./run_tests.sh unit

# Integration tests (requires API access)
./run_tests.sh integration

# With coverage
./run_tests.sh coverage

# Specific file
pytest tests/test_client.py -v
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

@pytest.mark.integration
@pytest.mark.slow
def test_api_integration():
    pass
```

Run specific markers:

```bash
pytest -m unit           # Only unit tests
pytest -m "not slow"     # Exclude slow tests
pytest -m "not live"     # Exclude live API tests
```

### Test Coverage

- Aim for 95%+ code coverage
- 100% coverage for new features
- Tests should be meaningful, not just for coverage

Check coverage:

```bash
./run_tests.sh coverage
# Then open htmlcov/index.html
```

## Pull Request Process

1. **Update Documentation**: Ensure all docs are updated
2. **Add Tests**: Include comprehensive tests
3. **Update CHANGELOG**: Add entry to CHANGELOG.md (if exists)
4. **Follow Template**: Fill out the PR template completely
5. **Request Review**: Tag maintainers for review
6. **Address Feedback**: Respond to review comments promptly
7. **Keep Updated**: Rebase on main if needed

### PR Title Format

- `feat: Add attachment upload support`
- `fix: Resolve MFA login error`
- `docs: Update installation instructions`
- `test: Add tests for edge cases`
- `refactor: Simplify error handling`

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed? Does it match lastpass-cli behavior?

## Changes
- List of changes made
- Breaking changes (if any)

## Testing
How was this tested? Include test commands used.

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No linting errors
- [ ] Coverage maintained at 95%+
```

## Style Guide

### Python Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints for function signatures
- Write docstrings for public APIs (Google style)

### Example

```python
def parse_blob(blob_data: bytes, encryption_key: bytes) -> List[Account]:
    """
    Parse the LastPass vault blob and decrypt accounts.
    
    Args:
        blob_data: The encrypted vault blob from LastPass server.
        encryption_key: The derived encryption key for decryption.
    
    Returns:
        A list of decrypted Account objects from the vault.
    
    Raises:
        DecryptionException: If blob cannot be decrypted.
        
    Example:
        >>> blob = download_blob(session)
        >>> accounts = parse_blob(blob, encryption_key)
        >>> for account in accounts:
        ...     print(account.name)
    """
    # Implementation...
    pass
```

## Documentation

### Updating Documentation

When making changes:

1. Update relevant `.md` files
2. Update docstrings
3. Add examples if needed
4. Update README if API changes

### Documentation Standards

- Use clear, simple language
- Include code examples
- Keep examples up to date
- Use proper Markdown formatting
- Reference lastpass-cli when relevant

## Community

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and discussions
- **Pull Requests**: For code contributions

### Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes
- Project documentation

## Questions?

If you have questions about contributing:

1. Check existing issues and discussions
2. Read the documentation
3. Ask in GitHub Discussions
4. Contact maintainers

Thank you for contributing! 🎉
