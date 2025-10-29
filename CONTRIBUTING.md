# Contributing to QC2Plus

Thank you for your interest in contributing to QC2Plus! 🎉

We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, code contributions, and more.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

---

## 📜 Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

**Key principles:**
- Be welcoming and inclusive
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community

---

## 🤝 How Can I Contribute?

### 🐛 Reporting Bugs

**Before submitting a bug report:**
- Check the [existing issues](https://github.com/YOUR_USERNAME/qc2plus/issues) to avoid duplicates
- Collect relevant information (version, OS, database type, error messages)

**When submitting a bug report, include:**
- **Clear title** describing the issue
- **QC2Plus version**: `qc2plus --version`
- **Python version**: `python --version`
- **Database type and version**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Error messages or logs**
- **Configuration files** (sanitize sensitive data!)

**Example:**
```markdown
## Bug: Statistical threshold test fails with NULL values

**Environment:**
- QC2Plus: 1.0.3
- Python: 3.9.7
- Database: PostgreSQL 14.2
- OS: Ubuntu 22.04

**Steps to Reproduce:**
1. Create model with statistical_threshold test
2. Run on table with NULL values in metric column
3. Error occurs

**Expected:** Test should handle NULLs gracefully
**Actual:** Crashes with TypeError

**Error:**
```
TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'
```

**Config:**
```yaml
statistical_threshold:
  metric: avg
  column_name: order_total  # Contains NULLs
```
```

### 💡 Suggesting Features

**Before suggesting a feature:**
- Check [existing feature requests](https://github.com/YOUR_USERNAME/qc2plus/issues?q=is%3Aissue+label%3Aenhancement)
- Consider if it fits QC2Plus's scope

**When suggesting a feature, include:**
- **Clear use case**: Why is this needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches?
- **Examples**: Show how it would be used

**Example:**
```markdown
## Feature Request: Support for MongoDB

**Use Case:**
Many organizations use MongoDB for operational data. Adding MongoDB support would enable quality checks on NoSQL databases.

**Proposed Solution:**
Add a MongoDB adapter in `qc2plus/adapters/mongodb.py` supporting:
- Connection via pymongo
- Level 1 tests (unique, not_null, etc.)
- Basic aggregation for statistical tests

**Example Usage:**
```yaml
database:
  type: mongodb
  connection_string: mongodb://localhost:27017
  database: mydb
```

**Alternatives:**
- Export MongoDB data to SQL first (current workaround)
- Use MongoDB's native validation rules (doesn't integrate with QC2Plus)
```

### 📝 Improving Documentation

Documentation improvements are always welcome! This includes:
- Fixing typos or unclear explanations
- Adding examples
- Improving code comments
- Translating documentation

**Small fixes:** Submit a PR directly  
**Large changes:** Open an issue first to discuss

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Git**
- **PostgreSQL** (for testing)
- **Docker** (optional, for full environment)

### Fork and Clone

```bash
# 1. Fork the repository on GitHub
# Click "Fork" at https://github.com/YOUR_USERNAME/qc2plus

# 2. Clone your fork
git clone https://github.com/YOUR_GITHUB_USERNAME/qc2plus.git
cd qc2plus

# 3. Add upstream remote
git remote add upstream https://github.com/YOUR_USERNAME/qc2plus.git

# 4. Verify remotes
git remote -v
# origin    https://github.com/YOUR_GITHUB_USERNAME/qc2plus.git (fetch)
# origin    https://github.com/YOUR_GITHUB_USERNAME/qc2plus.git (push)
# upstream  https://github.com/YOUR_USERNAME/qc2plus.git (fetch)
# upstream  https://github.com/YOUR_USERNAME/qc2plus.git (push)
```

---

## 💻 Development Setup

### Local Setup

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 2. Install in editable mode with dev dependencies
pip install -e ".[dev]"

# 3. Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install

# 4. Verify installation
qc2plus --version
pytest --version
```

### Development Dependencies

The `[dev]` extra installs:
- **pytest** - Testing framework
- **pytest-cov** - Code coverage
- **black** - Code formatter
- **flake8** - Linter
- **mypy** - Type checker
- **pre-commit** - Git hooks

### Docker Setup (Recommended)

```bash
# Start development environment
docker-compose up -d

# Access container
docker exec -it qc2plus-runner bash

# Inside container: run tests
pytest

# Inside container: run checks
cd examples/advanced
qc2plus run --target demo
```

### Database Setup (Local)

```bash
# Start PostgreSQL (if not using Docker)
sudo systemctl start postgresql

# Create test databases
createdb qc2plus_test
createdb qc2plus_results_test

# Load test data
psql -d qc2plus_test -f examples/data/init_tables.sql

# Set environment variable
export QC2PLUS_TEST_DB="postgresql://user:pass@localhost/qc2plus_test"
```

---

## ✏️ Making Changes

### Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests

### Write Code

1. **Write clean, readable code**
2. **Follow Python conventions** (PEP 8)
3. **Add type hints** where appropriate
4. **Write docstrings** for public functions
5. **Add tests** for new functionality

**Example:**

```python
def validate_email(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
```

### Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: Add email validation test"
```

**Commit message format:**
```
<type>: <short description>

<optional longer description>

<optional footer>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples:**
```bash
# Good commit messages
git commit -m "feat: Add MongoDB adapter support"
git commit -m "fix: Handle NULL values in statistical threshold"
git commit -m "docs: Update Docker Compose guide"
git commit -m "test: Add tests for email validation"

# Bad commit messages
git commit -m "update"
git commit -m "fixes"
git commit -m "WIP"
```

---

## 📤 Submitting Changes

### Before Submitting

```bash
# 1. Run tests
pytest

# 2. Check code coverage
pytest --cov=qc2plus --cov-report=term-missing

# 3. Format code
black qc2plus/

# 4. Lint code
flake8 qc2plus/

# 5. Type check
mypy qc2plus/

# 6. Update documentation if needed
```

### Push Changes

```bash
# Push to your fork
git push origin feature/your-feature-name
```

### Create Pull Request

1. Go to https://github.com/YOUR_USERNAME/qc2plus
2. Click "New Pull Request"
3. Select your branch
4. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to break)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added (if applicable)
- [ ] Code coverage maintained/improved

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review performed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

### PR Review Process

1. **Automated checks** run (tests, linting, coverage)
2. **Maintainer review** - may request changes
3. **Discussion** - address feedback
4. **Approval** - maintainer approves
5. **Merge** - changes merged into main

**Be patient!** Maintainers may take a few days to review.

---

## 🎨 Code Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# ✅ Good
def calculate_metric(
    values: list[float],
    window_size: int = 30
) -> float:
    """Calculate rolling average metric."""
    if not values:
        return 0.0
    return sum(values[-window_size:]) / len(values[-window_size:])

# ❌ Bad
def calc(vals, w=30):
    if not vals: return 0
    return sum(vals[-w:])/len(vals[-w:])
```

### Code Formatting

Use **Black** for consistent formatting:

```bash
# Format all files
black qc2plus/

# Format specific file
black qc2plus/level1/engine.py

# Check without modifying
black --check qc2plus/
```

### Linting

Use **flake8** to catch issues:

```bash
# Lint all files
flake8 qc2plus/

# Configuration in setup.cfg:
[flake8]
max-line-length = 100
ignore = E203, W503
exclude = .git, __pycache__, build, dist
```

### Type Hints

Add type hints for better code quality:

```python
from typing import Optional, List, Dict, Any

def run_test(
    model_name: str,
    test_config: Dict[str, Any],
    connection: Optional[Connection] = None
) -> List[TestResult]:
    """Run quality test on model."""
    pass
```

### Documentation

Write clear docstrings:

```python
def analyze_correlation(
    data: pd.DataFrame,
    variables: List[str],
    threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Analyze correlation between variables.
    
    Detects when correlation drops below expected threshold,
    indicating a relationship breakdown.
    
    Args:
        data: DataFrame with variable columns
        variables: List of column names to analyze
        threshold: Minimum expected correlation (0-1)
        
    Returns:
        Dictionary with:
            - 'status': 'pass' or 'fail'
            - 'current_correlation': float
            - 'expected_correlation': float
            - 'deviation': float
            
    Raises:
        ValueError: If variables not in DataFrame
        
    Example:
        >>> df = pd.DataFrame({'x': [1,2,3], 'y': [2,4,6]})
        >>> analyze_correlation(df, ['x', 'y'], 0.9)
        {'status': 'pass', 'current_correlation': 1.0, ...}
    """
    pass
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_level1/test_engine.py

# Run specific test
pytest tests/test_level1/test_engine.py::test_unique_validation

# Run with coverage
pytest --cov=qc2plus --cov-report=html

# Run with verbose output
pytest -v

# Run only failed tests
pytest --lf
```

### Writing Tests

```python
# tests/test_level1/test_validation.py
import pytest
from qc2plus.level1 import validation

def test_email_validation_valid():
    """Test email validation with valid email."""
    assert validation.validate_email("user@example.com") is True

def test_email_validation_invalid():
    """Test email validation with invalid email."""
    assert validation.validate_email("invalid") is False

def test_email_validation_empty():
    """Test email validation with empty string."""
    with pytest.raises(ValueError):
        validation.validate_email("")

@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("user.name@example.co.uk", True),
    ("invalid@", False),
    ("@example.com", False),
])
def test_email_validation_parametrized(email, expected):
    """Test email validation with multiple cases."""
    assert validation.validate_email(email) == expected
```

### Test Coverage

Aim for **>80% code coverage** for new code:

```bash
# Generate coverage report
pytest --cov=qc2plus --cov-report=html

# View report
open htmlcov/index.html
```

---

## 📚 Documentation

### Types of Documentation

1. **Code comments** - Explain complex logic
2. **Docstrings** - Document functions/classes
3. **README** - Project overview
4. **Guides** - How-to documentation
5. **API reference** - Complete parameter docs

### Updating Documentation

When adding features, update:
- [ ] Code docstrings
- [ ] README.md (if user-facing)
- [ ] QC2PLUS_DOCUMENTATION.md (API reference)
- [ ] Relevant guides in `docs/`
- [ ] Examples in `examples/`

### Building Documentation

```bash
# Install Sphinx (if using)
pip install sphinx sphinx-rtd-theme

# Build docs
cd docs
make html

# View docs
open _build/html/index.html
```

---

## 💬 Community

### Getting Help

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - Questions and general discussion
- **Documentation** - Check docs first!

### Communication

- Be respectful and professional
- Stay on topic
- Search before asking
- Provide context and details

### Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- Project README

---

## 🏆 Areas We Need Help

Current priorities:

- 🗄️ **Database Adapters** - MySQL, SQL Server, Oracle support
- 🧪 **Test Types** - New Level 1 validation tests
- 🤖 **ML Analyzers** - New Level 2 detection algorithms
- 📊 **Power BI Templates** - Pre-built dashboards
- 📝 **Documentation** - Tutorials and examples
- 🌐 **Translations** - Non-English documentation
- 🐛 **Bug Fixes** - Check open issues

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

---

## 🙏 Thank You!

Thank you for taking the time to contribute to QC2Plus! Every contribution, no matter how small, helps make the project better for everyone.

**Questions?** Feel free to ask in [GitHub Discussions](https://github.com/YOUR_USERNAME/qc2plus/discussions)!

---

**Happy Contributing! 🎉**