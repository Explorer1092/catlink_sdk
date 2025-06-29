# Publishing to PyPI

This guide explains how to publish the catlink-sdk package to PyPI.

## Method 1: Trusted Publisher (Recommended)

GitHub Actions can publish directly to PyPI using OpenID Connect (OIDC) without storing secrets.

### Setup Steps:

1. Go to [PyPI.org](https://pypi.org) and log in
2. Navigate to your account settings → Publishing
3. Add a new trusted publisher:
   - PyPI Project Name: `catlink-sdk`
   - Owner: `sss-ms` (or your GitHub username)
   - Repository name: `catlink_sdk`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

4. For Test PyPI, repeat the process at [test.pypi.org](https://test.pypi.org) with environment name: `testpypi`

### Publishing:

- **Automatic**: Create a GitHub release, and it will automatically publish to PyPI
- **Manual**: Go to Actions → "Publish to PyPI" → Run workflow → Enter version

## Method 2: API Token (Alternative)

If you prefer using API tokens:

### Setup Steps:

1. Generate API tokens:
   - PyPI: Go to [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
   - Test PyPI: Go to [test.pypi.org/manage/account/token/](https://test.pypi.org/manage/account/token/)

2. Add secrets to your GitHub repository:
   - Go to Settings → Secrets and variables → Actions
   - Add new repository secrets:
     - Name: `PYPI_API_TOKEN` → Value: Your PyPI token
     - Name: `TEST_PYPI_API_TOKEN` → Value: Your Test PyPI token

3. Update `.github/workflows/publish.yml`:
   - Uncomment the `password:` lines for both PyPI and Test PyPI sections

## Version Management

Before publishing, update the version in `pyproject.toml`:

```bash
# Bump patch version (0.1.0 → 0.1.1)
poetry version patch

# Bump minor version (0.1.0 → 0.2.0)
poetry version minor

# Bump major version (0.1.0 → 1.0.0)
poetry version major

# Set specific version
poetry version 1.2.3
```

## Testing Before Release

1. Run tests locally:
   ```bash
   poetry install
   poetry run pytest
   poetry run ruff check catlink_sdk/
   poetry run mypy catlink_sdk/
   ```

2. Build and check the package:
   ```bash
   poetry build
   poetry run twine check dist/*
   ```

3. Test installation:
   ```bash
   pip install dist/catlink_sdk-*.whl
   ```

## Manual Publishing (Local)

If needed, you can publish from your local machine:

```bash
# Configure PyPI credentials
poetry config pypi-token.pypi your-pypi-token

# Build and publish
poetry build
poetry publish

# For Test PyPI
poetry config repositories.test-pypi https://test.pypi.org/legacy/
poetry config pypi-token.test-pypi your-test-pypi-token
poetry publish -r test-pypi
```