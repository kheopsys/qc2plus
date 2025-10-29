# =============================================================================
# STEP 1: Prepare Environment
# =============================================================================

# Activate virtual environment
source venv/bin/activate

# Install build tools
pip install --upgrade pip build twine wheel

# Clean previous installation
pip uninstall qc2plus -y
pip cache purge

# =============================================================================
# STEP 2: Update Version (if version already exists on TestPyPI)
# =============================================================================

# Update version to 1.0.3 in all files
sed -i 's/1\.0\.2/1.0.3/g' setup.py pyproject.toml packaging/publish.sh qc2plus/__init__.py

# Verify version update
grep -E "(version|VERSION|__version__)" setup.py pyproject.toml packaging/publish.sh qc2plus/__init__.py | grep "1.0.3"

# =============================================================================
# STEP 3: Build and Verify Package
# =============================================================================

# Clean old builds
./packaging/publish.sh clean

# Build new package
./packaging/publish.sh build

# Test local installation
./packaging/publish.sh test

# Or do everything in one command
./packaging/publish.sh all

# =============================================================================
# STEP 4: Publish to TestPyPI
# =============================================================================

# Upload to TestPyPI
./packaging/publish.sh testpypi
# Type: yes

# Check on web: https://test.pypi.org/project/qc2plus/1.0.3/

# =============================================================================
# STEP 5: Test Installation from TestPyPI
# =============================================================================

# Create test environment
python -m venv test_env
source test_env/bin/activate

# Install from TestPyPI (use correct version: 1.0.3)
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            qc2plus==1.0.3

# Verify installation
qc2plus --version
python -c "import qc2plus; print('✅ Version:', qc2plus.__version__)"

# Test imports
python -c "from qc2plus.core import connection; print('✅ Imports OK')"

# Cleanup test environment
deactivate
rm -rf test_env

# =============================================================================
# STEP 6: Publish to PyPI Production (if TestPyPI OK)
# =============================================================================

# Reactivate main environment
source venv/bin/activate

# Publish to PyPI Production
./packaging/publish.sh pypi
# Type: PUBLISH

# Check on web: https://pypi.org/project/qc2plus/1.0.3/

# =============================================================================
# STEP 7: Final Verification from PyPI
# =============================================================================

# Create clean test environment
python -m venv final_test
source final_test/Script/activate

# Install from PyPI Production
pip install qc2plus==1.0.3

# Verify
qc2plus --version
python -c "import qc2plus; print('✅ PyPI installation OK!')"

# Cleanup
deactivate
rm -rf final_test