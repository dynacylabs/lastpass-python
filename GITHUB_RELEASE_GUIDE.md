# GitHub Release and PyPI Publishing Guide

This guide explains how to create GitHub releases that automatically publish to PyPI using **Trusted Publishing** (no API tokens needed!).

## Setup (One-Time)

### Step 1: Create GitHub Environment (Recommended for Security)

1. Go to your repository: https://github.com/dynacylabs/lastpass-py
2. Click **Settings** → **Environments**
3. Click **New environment**
4. Name: `pypi`
5. Click **Configure environment**
6. **Optional but recommended**: Add deployment protection rules
   - **Required reviewers**: Add yourself or team members who should approve releases
   - This prevents accidental publishes
7. Click **Save protection rules**

### Step 2: Manual First Upload

**Important**: You must do the initial manual upload first, then set up trusted publishing.

```bash
# Build and upload manually (creates the PyPI project)
rm -rf dist/ build/ *.egg-info/
python -m build
twine upload dist/*
```

### Step 3: Configure Trusted Publisher on PyPI

1. Go to https://pypi.org/manage/project/lastpass-py/settings/
2. Scroll to **Publishing** section
3. Click **Add a new publisher**
4. Fill in the form:
   - **PyPI Project Name**: `lastpass-py`
   - **Owner**: `dynacylabs`
   - **Repository name**: `lastpass-py`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: `pypi` (important: must match the GitHub environment)
5. Click **Add**

That's it! No API tokens needed. GitHub will authenticate using OpenID Connect (OIDC).

## How to Make a Release

### Method 1: GitHub UI (Easiest)

1. **Push your changes to main branch**
   ```bash
   git add .
   git commit -m "Prepare v1.0.0 release"
   git push origin main
   ```

2. **Create a new release on GitHub**
   - Go to https://github.com/dynacylabs/lastpass-py/releases/new
   - Click "Choose a tag" → Type `v1.0.0` → Click "Create new tag: v1.0.0 on publish"
   - Release title: `v1.0.0`
   - Description: Add release notes (features, bug fixes, breaking changes)
   - Click **Publish release**

3. **Automatic PyPI upload**
   - GitHub Actions will automatically build and upload to PyPI
   - Watch progress at: https://github.com/dynacylabs/lastpass-py/actions
   - Package will be live at: https://pypi.org/project/lastpass-py/

### Method 2: Command Line

1. **Commit and push your changes**
   ```bash
   git add .
   git commit -m "Prepare v1.0.0 release"
   git push origin main
   ```

2. **Create and push a tag**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **Create the release using GitHub CLI**
   ```bash
   gh release create v1.0.0 \
     --title "v1.0.0" \
     --notes "Initial release of lastpass-py

   Features:
   - Complete LastPass CLI implementation
   - Python API for vault access
   - 331+ tests with 95% coverage
   - AES-256 encryption support
   "
   ```

4. **Automatic PyPI upload**
   - GitHub Actions automatically builds and uploads
   - Check status: `gh run list`

## Release Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. You create a GitHub Release                              │
│    (either via GitHub UI or gh CLI)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. GitHub Actions automatically triggers                    │
│    (.github/workflows/publish-to-pypi.yml)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. GitHub Actions:                                          │
│    - Checks out code                                        │
│    - Installs Python and build tools                        │
│    - Builds the package (wheel + sdist)                     │
│    - Validates with twine check                             │
│    - Uploads to PyPI using your secret token                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Package is live on PyPI!                                 │
│    Users can: pip install lastpass-py                       │
└─────────────────────────────────────────────────────────────┘
```

## Version Bumping

Before each release, update the version in these files:

1. **pyproject.toml**
   ```toml
   version = "1.0.1"
   ```

2. **setup.py**
   ```python
   version="1.0.1",
   ```

3. **lastpass/__init__.py**
   ```python
   __version__ = "1.0.1"
   ```

**Tip**: Use semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

## Checking Release Status

### Via GitHub UI
- Go to: https://github.com/dynacylabs/lastpass-py/actions
- Click on the latest workflow run
- See real-time logs of build and upload

### Via Command Line
```bash
# List recent workflow runs
gh run list --workflow=publish-to-pypi.yml

# Watch a specific run
gh run watch

# View logs of latest run
gh run view --log
```

## Troubleshooting

### Build Fails
- Check the Actions log for specific errors
- Common issues: version conflicts, missing dependencies
- Fix locally, commit, and create a new release

### Upload Fails

**"Trusted publishing exchange failure"**
- The trusted publisher isn't configured on PyPI
- Go to https://pypi.org/manage/project/lastpass-py/settings/
- Add the publisher with correct repository details

**"403 Forbidden"**
- Repository name or owner doesn't match PyPI configuration
- Workflow name doesn't match (must be `publish-to-pypi.yml`)
- Verify settings on PyPI match your GitHub repository

**"400 Bad Request: Version already exists"**
- You cannot replace an existing version
- Bump the version number and create a new release

### Workflow Doesn't Trigger
- Ensure you created a **Release**, not just a tag
- The workflow triggers on `release: [published]` events
- Check Actions tab for any error messages

## Security with Trusted Publishing

✅ **Benefits**:
- No API tokens to manage or rotate
- No secrets stored in GitHub
- Uses OpenID Connect (OIDC) for authentication
- GitHub cryptographically proves the workflow's identity
- Automatically secured and maintained by GitHub + PyPI

✅ **How It Works**:
1. You create a GitHub release
2. GitHub generates a temporary OIDC token for the workflow
3. PyPI verifies the token matches your configured publisher
4. Upload succeeds if everything matches
5. Token expires immediately after use

✅ **What's Protected**:
- Only workflows from your specified repository can publish
- Only the specified workflow file can publish
- Only releases (not manual runs) can publish
- PyPI verifies the exact GitHub repository and workflow

## Testing Before Release

Create a pre-release to test without affecting the main release:

1. Tag with suffix: `v1.0.0-beta.1`
2. Mark as "pre-release" in GitHub
3. Test installation: `pip install lastpass-py --pre`
4. If good, create the real release

## Example Release Notes Template

```markdown
## What's New in v1.0.0

### Features
- ✨ New command: `lpass export --format json`
- 🔐 Added support for TOTP codes

### Bug Fixes
- 🐛 Fixed login timeout on slow connections
- 🐛 Resolved clipboard clearing issue on macOS

### Documentation
- 📚 Added API usage examples
- 📚 Improved CLI command reference

### Breaking Changes
- ⚠️ Removed deprecated `--insecure` flag
- ⚠️ Changed default config location to XDG standard

**Full Changelog**: https://github.com/dynacylabs/lastpass-py/compare/v0.9.0...v1.0.0
```
