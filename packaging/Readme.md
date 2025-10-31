# 📦 QC2Plus - Packaging & Build Process

Quick reference guide for building and publishing the qc2plus package.

---

## 🚀 Quick Build Process

### Prerequisites
```bash
pip install build twine
```

### 1. Increment Version
```bash
# Example: 1.0.3 → 1.0.4
NEW_VERSION="1.0.4"

sed -i "s/version = \"[0-9.]*\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i "s/version=\"[0-9.]*\"/version=\"$NEW_VERSION\"/" setup.py

# Verify
grep "version" pyproject.toml
grep "version=" setup.py
```

### 2. Clean Previous Builds
```bash
rm -rf build/ dist/ *.egg-info
```

⚠️ **DO NOT DELETE:**
- `qc2plus/` (source code)
- `*.py` files

### 3. Build Package
```bash
python -m build
```

Creates:
- `dist/qc2plus-1.0.4-py3-none-any.whl`
- `dist/qc2plus-1.0.4.tar.gz`

### 4. Verify Package Content
```bash
# List wheel contents
unzip -l dist/qc2plus-1.0.4-py3-none-any.whl | grep "qc2plus/.*\.py" | head -20
```

✅ **Must see:**
```
qc2plus/__init__.py
qc2plus/cli.py
qc2plus/core/__init__.py
qc2plus/core/connection.py
qc2plus/level1/engine.py
...
```

❌ **If no .py files:** Check `[tool.setuptools]` in `pyproject.toml`

### 5. Verify Dependencies
```bash
unzip -p dist/qc2plus-1.0.4-py3-none-any.whl qc2plus-1.0.4.dist-info/METADATA | grep "Requires-Dist"
```

✅ **Must include:**
```
Requires-Dist: jinja2>=3.0.0
Requires-Dist: click>=8.0.0
Requires-Dist: sqlalchemy>=1.4.0
...
```

### 6. Test Locally
```bash
# Create clean test environment
cd ~
mkdir test_qc2plus_local
cd test_qc2plus_local
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux/Mac

# Install local wheel
pip install ~/work_repo/qc2/qc2plus-internal/dist/qc2plus-1.0.4-py3-none-any.whl

# Test
python -c "import qc2plus; from qc2plus.core.connection import ConnectionManager; print('✅ OK')"
qc2plus --help
```

✅ **If all tests pass** → Proceed to publish

### 7. Publish to TestPyPI
```bash
python -m twine upload --repository testpypi dist/*
```

View at: `https://test.pypi.org/project/qc2plus/1.0.4/`

### 8. Test from TestPyPI
```bash
# New clean environment
cd ~
mkdir test_from_testpypi
cd test_from_testpypi
python -m venv venv
source venv/Scripts/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            qc2plus==1.0.4

# Wait 2-5 minutes if "version not found"

# Test
qc2plus --help
python -c "import qc2plus; print('✅ OK')"
```

### 9. Publish to PyPI (Production)
⚠️ **Only after successful TestPyPI tests!**

```bash
python -m twine upload dist/*
```

View at: `https://pypi.org/project/qc2plus/1.0.4/`

---

## 🔄 Complete Workflow (Copy-Paste)

```bash
# 1. Increment version
NEW_VERSION="1.0.4"
sed -i "s/version = \"[0-9.]*\"/version = \"$NEW_VERSION\"/" pyproject.toml
sed -i "s/version=\"[0-9.]*\"/version=\"$NEW_VERSION\"/" setup.py

# 2. Clean & build
rm -rf build/ dist/ *.egg-info
python -m build

# 3. Verify content
unzip -l dist/qc2plus-$NEW_VERSION-py3-none-any.whl | grep "qc2plus/.*\.py"

# 4. Test local
pip install dist/qc2plus-$NEW_VERSION-py3-none-any.whl --force-reinstall
qc2plus --help

# 5. Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# 6. Test from TestPyPI (in new terminal/environment)
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            qc2plus==$NEW_VERSION

# 7. Upload to PyPI (if all OK)
python -m twine upload dist/*
```

---

## 📋 Pre-Publish Checklist

- [ ] Version incremented in `pyproject.toml` AND `setup.py`
- [ ] All `__init__.py` files present in subdirectories
- [ ] `[tool.setuptools]` section in `pyproject.toml`
- [ ] `python -m build` succeeded
- [ ] `.py` files present in wheel (verify with `unzip -l`)
- [ ] All dependencies in `pyproject.toml` dependencies list
- [ ] Local installation test passed
- [ ] `qc2plus --help` works
- [ ] TestPyPI installation test passed

---

## 🐛 Common Issues

### Issue: Empty Package (no .py files)

**Cause:** Missing `[tool.setuptools]` in `pyproject.toml`

**Fix:**
```bash
cat >> pyproject.toml << 'EOF'

[tool.setuptools]
packages = ["qc2plus", "qc2plus.core", "qc2plus.level1", "qc2plus.level2", "qc2plus.alerting", "qc2plus.persistence", "qc2plus.sql"]
EOF
```

### Issue: Missing Dependencies (e.g., jinja2)

**Cause:** Incomplete dependencies list in `pyproject.toml`

**Fix:** Ensure all required packages are in `dependencies = [...]`

### Issue: ModuleNotFoundError after install

**Cause:** Missing `__init__.py` files

**Fix:**
```bash
touch qc2plus/__init__.py
touch qc2plus/core/__init__.py
touch qc2plus/level1/__init__.py
touch qc2plus/level2/__init__.py
touch qc2plus/alerting/__init__.py
touch qc2plus/persistence/__init__.py
```

### Issue: "File already exists" error

**Solution:** Cannot republish same version. Increment version:
```bash
# 1.0.4 → 1.0.5
sed -i 's/version = "1.0.4"/version = "1.0.5"/' pyproject.toml
sed -i 's/version="1.0.4"/version="1.0.5"/' setup.py
```

---

## 🔢 Version Management

### Semantic Versioning (SemVer)
```
MAJOR.MINOR.PATCH
  |     |     |
  |     |     └─ Bug fixes (1.0.1 → 1.0.2)
  |     └─────── New features (1.0.2 → 1.1.0)
  └───────────── Breaking changes (1.1.0 → 2.0.0)
```

### Update Version
```bash
# Method 1: Manual
sed -i 's/version = "1.0.3"/version = "1.0.4"/' pyproject.toml
sed -i 's/version="1.0.3"/version="1.0.4"/' setup.py

# Method 2: Script (if available)
./scripts/bump_version.sh 1.0.4
```

---

## 📁 Required Files

```
qc2plus-internal/
├── setup.py                    # Build config
├── pyproject.toml              # Modern config (PRIORITY)
├── MANIFEST.in                 # Include/exclude files
├── requirements.txt            # Dependencies
├── README.md
├── LICENSE
└── qc2plus/
    ├── __init__.py            # ⚠️ REQUIRED
    ├── cli.py
    ├── core/
    │   ├── __init__.py        # ⚠️ REQUIRED
    │   └── ...
    └── ...
```

---

## 🔐 PyPI Tokens Setup

### ~/.pypirc
```ini
[testpypi]
username = __token__
password = pypi-AgENdGVzdC...

[pypi]
username = __token__
password = pypi-AgEIcHlwaS...
```

---

## 📚 Key Configuration Files

### pyproject.toml (Essential sections)
```toml
[project]
name = "qc2plus"
version = "1.0.4"
dependencies = [
    "jinja2>=3.0.0",
    "click>=8.0.0",
    # ... all dependencies
]

[tool.setuptools]
packages = ["qc2plus", "qc2plus.core", "qc2plus.level1", ...]
```

### MANIFEST.in
```
include README.md
include LICENSE
include requirements.txt
recursive-include qc2plus/level1/templates *.sql
recursive-include qc2plus/templates *.yml
prune tests
prune examples
```

---

## 🎯 Example: Release v1.0.5

```bash
# Complete workflow
sed -i 's/version = "1.0.4"/version = "1.0.5"/' pyproject.toml
sed -i 's/version="1.0.4"/version="1.0.5"/' setup.py
rm -rf build/ dist/ *.egg-info
python -m build
unzip -l dist/qc2plus-1.0.5-py3-none-any.whl | grep "qc2plus/.*\.py"
pip install dist/qc2plus-1.0.5-py3-none-any.whl --force-reinstall
qc2plus --help
python -m twine upload --repository testpypi dist/*
# Test from TestPyPI
python -m twine upload dist/*  # To PyPI if all OK
```

---

**📦 Happy Packaging! 🚀**