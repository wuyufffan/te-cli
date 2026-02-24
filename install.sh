#!/bin/bash
#
# te-cli Installation Script
#

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BIN="${HOME}/.local/bin"
INSTALL_SHARE="${HOME}/.local/share/te-cli"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    print_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [[ "$MAJOR" -lt 3 ]] || [[ "$MAJOR" -eq 3 && "$MINOR" -lt 10 ]]; then
        print_error "Python 3.10+ required, found $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

# Create directories
print_info "Creating directories..."
mkdir -p "$INSTALL_BIN"
mkdir -p "$INSTALL_SHARE"
print_success "Directories created"

# Copy Python code
print_info "Installing te-cli to $INSTALL_SHARE..."
rm -rf "$INSTALL_SHARE"
cp -r "$REPO_DIR" "$INSTALL_SHARE/"
print_success "te-cli installed"

# Create wrapper script
print_info "Creating wrapper script..."

cat > "$INSTALL_BIN/te" << 'EOF'
#!/bin/bash
TE_CLI_SHARE="${HOME}/.local/share/te-cli"

if [[ ! -d "$TE_CLI_SHARE" ]]; then
    echo "Error: te-cli not properly installed."
    exit 1
fi

export PYTHONPATH="${TE_CLI_SHARE}:${PYTHONPATH}"
cd "${TE_CLI_SHARE}"
exec python3 -c "
import sys
sys.path.insert(0, '${TE_CLI_SHARE}')

from install_config import setup_config_if_needed
from cli import main

te_path = setup_config_if_needed()
if te_path is None:
    sys.exit(1)

sys.exit(main())
" "$@"
EOF

chmod +x "$INSTALL_BIN/te"
print_success "Wrapper script created"

# Check PATH
if [[ ":$PATH:" != *":$INSTALL_BIN:"* ]]; then
    print_warning "$INSTALL_BIN is not in your PATH"
    echo "Add it to your PATH:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ te-cli installed successfully${NC}"
echo "=================================================="
echo ""
echo "Installed components:"
echo "  - te command: $INSTALL_BIN/te"
echo "  - Python code: $INSTALL_SHARE/"
echo ""
echo "Next steps:"
echo "  1. Ensure $INSTALL_BIN is in your PATH"
echo "  2. Run 'te --help' to configure"
echo ""
