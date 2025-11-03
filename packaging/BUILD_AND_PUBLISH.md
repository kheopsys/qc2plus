# 🏗️ Build & Publication Guide for 2QC+

This guide covers building, packaging, and publishing the 2QC+ Data Quality Framework.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Building the Package](#building-the-package)
4. [Testing the Build](#testing-the-build)
5. [Publishing to PyPI](#publishing-to-pypi)
6. [Complete Release Example](#complete-release-example)
7. [Docker Build & Publishing](#docker-build--publishing)
8. [Version Management](#version-management)
9. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Tools

```bash
# Install build tools
pip install --upgrade pip setuptools wheel build twine

# For development and testing
pip install -r requirements-dev.txt
```

### Required Accounts

- **PyPI Account**: [https://pypi.org/account/register/](https://pypi.org/account/register/)
- **TestPyPI Account** (for testing): [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)
- **Docker Hub Account** (optional): [https://hub.docker.com/signup](https://hub.docker.com/signup)

---

## 📁 Project Structure

```
qc2plus/
├── qc2plus/                 # Main package source code
│   ├── __init__.py
│   ├── cli/                 # CLI commands
│   ├── core/                # Core functionality
│   ├── level1/              # Level 1 tests
│   │   └── templates/       # SQL templates
│   ├── level2/              # Level 2 analyzers
│   ├── alerting/            # Alerting system
│   └── persistence/         # Database persistence
├── tests/                   # Test suite
├── examples/                # Example projects
│   ├── basic/
│   └── advanced/
├── docs/                    # Documentation
├── setup.py                 # Package configuration (setuptools)
├── pyproject.toml          # Build system configuration (modern)
├── setup.cfg               # Legacy configuration
├── MANIFEST.in             # Package data files
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Development dependencies
├── README.md               # Main documentation
├── LICENSE                 # MIT License
├── CHANGELOG.md            # Version history
├── .env.example            # Environment variables template
└── Dockerfile              # Docker image configuration
```

---

## 🔨 Building the Package

### 1. Update Version Number

Update version in **both** files:

**pyproject.toml:**
```toml
[project]
name = "qc2plus"
version = "1.0.5"  # Update this
```

**setup.py:**
```python
setup(
    name="qc2plus",
    version="1.0.5",  # Update this
    # ...
)
```

### 2. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info/

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 3. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=qc2plus --cov-report=html

# Check code quality
black qc2plus/ --check
flake8 qc2plus/
mypy qc2plus/
```

### 4. Build the Package

```bash
# Build source distribution and wheel
python -m build

# This creates:
# - dist/qc2plus-1.0.5.tar.gz (source)
# - dist/qc2plus-1.0.5-py3-none-any.whl (wheel)
```

### 5. Verify the Build

```bash
# Check wheel contents
unzip -l dist/qc2plus-1.0.5-py3-none-any.whl | grep "qc2plus/.*\.py"

# Verify all Python files are included
unzip -l dist/qc2plus-1.0.5-py3-none-any.whl | grep -E "(cli|core|level1|level2|alerting|persistence)"

# Check package metadata
twine check dist/*
```

**Expected output:**
```
Checking dist/qc2plus-1.0.5-py3-none-any.whl: PASSED
Checking dist/qc2plus-1.0.5.tar.gz: PASSED
```

---

## 🧪 Testing the Build

### Test Local Installation

```bash
# Install from wheel
pip install dist/qc2plus-1.0.5-py3-none-any.whl --force-reinstall

# Test the CLI
qc2plus --help
qc2plus --version

# Test with example project
cd examples/basic
qc2plus test-connection --target dev
qc2plus run --target dev
```

### Test with TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    qc2plus

# Test the installation
qc2plus --version
qc2plus --help
```

---

## 📦 Publishing to PyPI

### 1. Configure PyPI Credentials

Create or update `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
```

**Security**: Protect this file:
```bash
chmod 600 ~/.pypirc
```

### 2. Generate API Tokens

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens"
3. Click "Add API token"
4. Set scope to "Entire account" or specific project
5. Copy the token (starts with `pypi-`)

### 3. Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*

# Enter your credentials when prompted
# Or use token from ~/.pypirc
```

### 4. Verify Publication

```bash
# Check on PyPI
open https://pypi.org/project/qc2plus/

# Install from PyPI
pip install qc2plus

# Test installation
qc2plus --version
```

---

## 🚀 Complete Release Example

### Example: Release v1.0.5

Here's a **complete step-by-step workflow** for releasing version 1.0.5:

```bash
# Step 1: Update version numbers
sed -i 's/version = "1.0.4"/version = "1.0.5"/' pyproject.toml
sed -i 's/version="1.0.4"/version="1.0.5"/' setup.py

# Step 2: Clean old builds
rm -rf build/ dist/ *.egg-info/

# Step 3: Build the package
python -m build

# Step 4: Verify wheel contents (check all Python files are included)
unzip -l dist/qc2plus-1.0.5-py3-none-any.whl | grep "qc2plus/.*\.py"

# Expected output should show:
# - qc2plus/__init__.py
# - qc2plus/cli/*.py
# - qc2plus/core/*.py
# - qc2plus/level1/*.py
# - qc2plus/level2/*.py
# - qc2plus/alerting/*.py
# - qc2plus/persistence/*.py

# Step 5: Test local installation
pip install dist/qc2plus-1.0.5-py3-none-any.whl --force-reinstall

# Step 6: Verify CLI works
qc2plus --help
qc2plus --version  # Should output: qc2plus version 1.0.5

# Step 7: Upload to TestPyPI (for testing)
python -m twine upload --repository testpypi dist/*

# Step 8: Test installation from TestPyPI (optional but recommended)
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    qc2plus==1.0.5 --force-reinstall

# Step 9: Run a quick test
qc2plus --help

# Step 10: If everything looks good, upload to production PyPI
python -m twine upload dist/*

# Step 11: Create and push git tag
git tag -a v1.0.5 -m "Release version 1.0.5"
git push origin v1.0.5

# Step 12: Verify on PyPI
# Visit: https://pypi.org/project/qc2plus/1.0.5/

# Step 13: Test final installation
pip install qc2plus==1.0.5
qc2plus --version
```

### One-Liner Quick Release (for experienced users)

```bash
# Quick release workflow (use with caution!)
sed -i 's/version = "1.0.4"/version = "1.0.5"/' pyproject.toml && \
sed -i 's/version="1.0.4"/version="1.0.5"/' setup.py && \
rm -rf build/ dist/ *.egg-info/ && \
python -m build && \
twine check dist/* && \
pip install dist/qc2plus-1.0.5-py3-none-any.whl --force-reinstall && \
qc2plus --help && \
python -m twine upload --repository testpypi dist/* && \
python -m twine upload dist/*
```

---

## 🐳 Docker Build & Publishing

### 1. Build Docker Image

```bash
# Build for local architecture
docker build -t qc2plus:1.0.5 .

# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t qc2plus:1.0.5 \
  --push .
```

### 2. Tag for Docker Hub

```bash
# Tag with version
docker tag qc2plus:1.0.5 kheopsys/qc2plus:1.0.5
docker tag qc2plus:1.0.5 kheopsys/qc2plus:latest

# Tag with minor version
docker tag qc2plus:1.0.5 kheopsys/qc2plus:1.0
docker tag qc2plus:1.0.5 kheopsys/qc2plus:1
```

### 3. Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push all tags
docker push kheopsys/qc2plus:1.0.5
docker push kheopsys/qc2plus:latest
docker push kheopsys/qc2plus:1.0
docker push kheopsys/qc2plus:1
```

### 4. Test Docker Image

```bash
# Pull and test
docker pull kheopsys/qc2plus:latest

# Run container
docker run --rm kheopsys/qc2plus:latest qc2plus --version

# Test with docker-compose
docker-compose up -d
docker-compose exec qc2plus-runner qc2plus --help
```

---

## 🔢 Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.1.x): New features, backward compatible
- **PATCH** (x.x.1): Bug fixes, backward compatible

Current version: **1.0.5**

### Version Workflow

```bash
# 1. Update version in pyproject.toml and setup.py
sed -i 's/version = "1.0.4"/version = "1.0.5"/' pyproject.toml
sed -i 's/version="1.0.4"/version="1.0.5"/' setup.py

# 2. Update CHANGELOG.md
# Add release notes manually

# 3. Commit version bump
git add pyproject.toml setup.py CHANGELOG.md
git commit -m "Bump version to 1.0.5"

# 4. Create git tag
git tag -a v1.0.5 -m "Release version 1.0.5"

# 5. Push to repository
git push origin main
git push origin v1.0.5

# 6. Build and publish
python -m build
python -m twine upload dist/*
```

---

## 🐛 Troubleshooting

### Build Issues

**Problem**: `ModuleNotFoundError` during build

```bash
# Solution: Ensure all dependencies are installed
pip install -r requirements.txt
```

**Problem**: `error: invalid command 'bdist_wheel'`

```bash
# Solution: Install wheel
pip install wheel
```

**Problem**: Files missing from wheel

```bash
# Solution: Check MANIFEST.in and setup.py package_data
# Verify with:
unzip -l dist/qc2plus-*.whl
```

### Upload Issues

**Problem**: `HTTPError: 403 Forbidden`

```bash
# Solution: Check credentials or use API token
twine upload --verbose dist/*
```

**Problem**: `File already exists`

```bash
# Solution: Version already published, increment version
# Edit pyproject.toml and setup.py, then rebuild
```

**Problem**: `Invalid distribution filename`

```bash
# Solution: Ensure version numbers match in both files
grep version pyproject.toml
grep version setup.py
```

### Docker Issues

**Problem**: `permission denied` on docker commands

```bash
# Solution: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Problem**: Multi-arch build fails

```bash
# Solution: Setup buildx
docker buildx create --use
docker buildx inspect --bootstrap
```

---

## 📝 Release Checklist

Before each release:

- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Code quality checks pass (`black`, `flake8`, `mypy`)
- [ ] Documentation updated (README.md)
- [ ] CHANGELOG.md updated with new version
- [ ] Version bumped in `pyproject.toml` **and** `setup.py`
- [ ] Clean build artifacts (`rm -rf build/ dist/ *.egg-info/`)
- [ ] Built successfully (`python -m build`)
- [ ] Wheel verified (`unzip -l dist/*.whl`)
- [ ] Package checked (`twine check dist/*`)
- [ ] Tested locally (`pip install dist/*.whl`)
- [ ] CLI works (`qc2plus --help`, `qc2plus --version`)
- [ ] Uploaded to TestPyPI and tested
- [ ] Uploaded to PyPI
- [ ] Git tag created and pushed
- [ ] Docker image built and pushed (optional)
- [ ] Release notes created on GitHub

---

## 🔒 Security Best Practices

1. **Never commit credentials**
   - Use `.env` files (add to `.gitignore`)
   - Use environment variables
   - Use API tokens instead of passwords

2. **Protect API tokens**
   - Store in `~/.pypirc` with `chmod 600`
   - Use GitHub Secrets for CI/CD
   - Rotate tokens regularly

3. **Sign releases** (optional)
   ```bash
   # Sign with GPG
   gpg --detach-sign -a dist/qc2plus-1.0.5.tar.gz
   twine upload dist/* --sign
   ```

4. **Verify downloads**
   ```bash
   # Verify package integrity
   pip install qc2plus --hash sha256:EXPECTED_HASH
   ```

---

## 📊 Package Structure Verification

### Essential Files in Wheel

The built wheel should contain:

```
qc2plus/
├── __init__.py
├── cli/
│   ├── __init__.py
│   └── main.py
├── core/
│   ├── __init__.py
│   ├── connection.py
│   ├── project.py
│   └── runner.py
├── level1/
│   ├── __init__.py
│   ├── engine.py
│   └── templates/
│       └── *.sql
├── level2/
│   ├── __init__.py
│   ├── correlation.py
│   ├── temporal.py
│   ├── distribution.py
│   └── anomaly_filter.py
├── alerting/
│   ├── __init__.py
│   └── alerts.py
└── persistence/
    ├── __init__.py
    └── persistence.py
```

### Verify with:

```bash
# Check structure
unzip -l dist/qc2plus-1.0.5-py3-none-any.whl

# Count Python files
unzip -l dist/qc2plus-1.0.5-py3-none-any.whl | grep "\.py$" | wc -l

# Check specific modules
unzip -l dist/qc2plus-1.0.5-py3-none-any.whl | grep -E "(cli|core|level1|level2|alerting|persistence)"
```

---

## 📚 Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Semantic Versioning](https://semver.org/)
- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)

---

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/kheopsys/qc2plus-internal/issues)
- **Documentation**: [README.md](https://github.com/kheopsys/qc2plus-internal/README.md)
- **Email**: contact-qc2plus@kheopsys.com

---

## 📝 Notes

- Current stable version: **1.0.5**
- Python compatibility: **3.9+**
- License: **MIT**
- Repository: [kheopsys/qc2plus-internal](https://github.com/kheopsys/qc2plus)

---

**Last Updated**: 2025-10-28
