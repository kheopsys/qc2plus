#!/bin/bash
# =============================================================================
# qc2plus PyPI Publication Script (Simplified)
# =============================================================================
# Usage: ./publish.sh [testpypi|pypi]
# =============================================================================

set -e  # Exit on error

VERSION="1.0.3"
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Publishing qc2plus v${VERSION} ===${NC}"

# Function to print messages
info() { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }
warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# Check if version matches in files
check_version() {
    info "Checking versions..."
    
    setup_version=$(grep 'version=' setup.py | head -1 | sed 's/.*version="\(.*\)".*/\1/')
    pyproject_version=$(grep 'version =' pyproject.toml | head -1 | sed 's/.*version = "\(.*\)".*/\1/')
    
    if [ "$setup_version" != "$VERSION" ] || [ "$pyproject_version" != "$VERSION" ]; then
        error "Version mismatch! setup.py: $setup_version, pyproject.toml: $pyproject_version, expected: $VERSION"
    fi
    
    success "Versions verified: $VERSION"
}

# Clean old builds
clean() {
    info "Cleaning old builds..."
    rm -rf build/ dist/ *.egg-info/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    success "Cleanup completed"
}

# Build package
build() {
    info "Building package..."
    python -m build || error "Build failed"
    success "Package built successfully"
}

# Check build
check() {
    info "Checking build..."
    
    # Check with twine
    twine check dist/* || error "Twine check failed"
    
    # Check wheel contents
    wheel_file="dist/qc2plus-${VERSION}-py3-none-any.whl"
    if [ ! -f "$wheel_file" ]; then
        error "Wheel file not found: $wheel_file"
    fi
    
    # Count Python files in wheel
    py_count=$(unzip -l "$wheel_file" | grep "qc2plus/.*\.py$" | wc -l)
    info "Python files in wheel: $py_count"
    
    if [ "$py_count" -lt 5 ]; then
        warning "Few Python files detected ($py_count). Please verify contents."
    fi
    
    success "Build verified"
}

# Test local installation
test_local() {
    info "Testing local installation..."
    
    pip install "dist/qc2plus-${VERSION}-py3-none-any.whl" --force-reinstall --quiet
    
    # Test CLI
    if ! command -v qc2plus &> /dev/null; then
        error "qc2plus command not found after installation"
    fi
    
    # Test version
    installed_version=$(qc2plus --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    if [ "$installed_version" != "$VERSION" ]; then
        error "Version mismatch after installation: got $installed_version, expected $VERSION"
    fi
    
    success "Local installation tested successfully"
}

# Upload to TestPyPI
upload_testpypi() {
    warning "Uploading to TestPyPI..."
    read -p "Continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        info "Upload cancelled"
        exit 0
    fi
    
    python -m twine upload --repository testpypi dist/* || error "Upload to TestPyPI failed"
    
    success "Uploaded to TestPyPI: https://test.pypi.org/project/qc2plus/${VERSION}/"
    info "Test with: pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ qc2plus==${VERSION}"
}

# Upload to PyPI
upload_pypi() {
    warning "⚠️  WARNING: Uploading to PyPI PRODUCTION!"
    warning "⚠️  This action is IRREVERSIBLE!"
    echo ""
    read -p "Are you SURE you want to publish v${VERSION} to PyPI? (type 'PUBLISH'): " confirm
    
    if [ "$confirm" != "PUBLISH" ]; then
        info "Publication cancelled"
        exit 0
    fi
    
    python -m twine upload dist/* || error "Upload to PyPI failed"
    
    success "✅ Published to PyPI: https://pypi.org/project/qc2plus/${VERSION}/"
    success "✅ Install with: pip install qc2plus==${VERSION}"
}

# Main workflow
case "${1:-help}" in
    clean)
        clean
        ;;
    build)
        check_version
        clean
        build
        check
        ;;
    test)
        check_version
        test_local
        ;;
    testpypi)
        check_version
        clean
        build
        check
        test_local
        upload_testpypi
        ;;
    pypi)
        check_version
        clean
        build
        check
        test_local
        upload_pypi
        ;;
    all)
        check_version
        clean
        build
        check
        test_local
        success "Ready for publication!"
        info "Run './publish.sh testpypi' to test or './publish.sh pypi' to publish"
        ;;
    help|*)
        cat << EOF
Usage: ./publish.sh [command]

Commands:
    clean       - Clean build artifacts
    build       - Build the package
    test        - Test local installation
    testpypi    - Publish to TestPyPI (for testing)
    pypi        - Publish to PyPI (PRODUCTION)
    all         - Prepare everything (clean + build + check + test)
    help        - Show this help message

Examples:
    ./publish.sh all        # Prepare everything
    ./publish.sh testpypi   # Test on TestPyPI
    ./publish.sh pypi       # Publish to production

Current version: ${VERSION}
EOF
        ;;
esac