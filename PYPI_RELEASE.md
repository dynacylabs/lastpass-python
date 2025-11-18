# PyPI Release Instructions for `lastpass-py`

This document contains instructions for publishing the `lastpass-py` package to PyPI.

## Pre-Release Checklist

All items below have been completed:

- ✅ Package name changed from `lastpass-python` to `lastpass-py`
- ✅ Repository URLs updated to `https://github.com/dynacylabs/lastpass-py`
- ✅ README.md updated with new package name and PyPI installation instructions
- ✅ User-Agent string updated to `lpass-cli/1.0.0`
- ✅ MANIFEST.in updated to include correct files
- ✅ No syntax errors in configuration files

## Package Information

- **Package Name**: `lastpass-py`
- **Version**: 1.0.0
- **Repository**: https://github.com/dynacylabs/lastpass-py
- **License**: GPL-2.0-or-later
- **Python Support**: 3.8+

## Build and Upload Instructions

### 1. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info/
```

### 2. Build the Package

```bash
python -m build
```

This will create:
- `dist/lastpass_py-1.0.0.tar.gz` (source distribution)
- `dist/lastpass_py-1.0.0-py3-none-any.whl` (wheel distribution)

### 3. Check the Package

Verify the package with twine:

```bash
twine check dist/*
```

### 4. Test Upload to TestPyPI (Recommended)

First test on TestPyPI to ensure everything works:

```bash
twine upload --repository testpypi dist/*
```

Then test installation:

```bash
pip install --index-url https://test.pypi.org/simple/ lastpass-py
```

### 5. Upload to PyPI

Once verified on TestPyPI, upload to the real PyPI:

```bash
twine upload dist/*
```

You will be prompted for your PyPI credentials. Alternatively, use an API token:

```bash
twine upload dist/* --username __token__ --password pypi-YOUR_TOKEN_HERE
```

### 6. Verify Installation

After upload, verify the package can be installed:

```bash
pip install lastpass-py
```

## Post-Release Tasks

1. **Tag the Release**: Create a git tag for the release
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Create GitHub Release**: Create a release on GitHub with release notes

3. **Update Documentation**: Ensure all documentation references the new package name

4. **Announce**: Announce the package availability

## PyPI Package Page

After publishing, the package will be available at:
- https://pypi.org/project/lastpass-py/

## Troubleshooting

### If the package name is already taken

If `lastpass-py` is already taken on PyPI, you may need to:
1. Choose a different name (e.g., `pylpass`, `python-lastpass`)
2. Contact PyPI support if you believe you have rights to the name
3. Update the package name in `pyproject.toml` and `setup.py`

### Authentication Issues

For uploading, you can use:
- Username/password authentication
- API tokens (recommended): https://pypi.org/help/#apitoken

Configure tokens in `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
username = __token__
password = pypi-your-test-token-here
```

## Package Structure

The package includes:
- Core library in `lastpass/` directory
- CLI tool accessible via `lpass` command
- Type stubs (`py.typed`)
- Comprehensive test suite
- Full documentation in README.md

## Dependencies

**Runtime**:
- requests >= 2.28.0
- pycryptodome >= 3.15.0

**Optional**:
- pyperclip >= 1.8.0 (for clipboard support)

**Development**:
- pytest >= 7.0.0
- pytest-cov >= 3.0.0
- pytest-mock >= 3.10.0
- responses >= 0.22.0
- black >= 22.0.0
- flake8 >= 4.0.0
- mypy >= 0.950
