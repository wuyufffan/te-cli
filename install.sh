#!/bin/bash
#
# te-cli 安装脚本
#

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BIN="${HOME}/.local/bin"
INSTALL_SHARE="${HOME}/.local/share"
TE_INSTALL_DIR="${INSTALL_SHARE}/te-cli"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查 Python 版本
check_python() {
    print_info "检查 Python 版本..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "未安装 Python 3"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [[ "$MAJOR" -lt 3 ]] || [[ "$MAJOR" -eq 3 && "$MINOR" -lt 10 ]]; then
        print_error "te-cli 需要 Python 3.10+，当前版本 $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION 检测通过"
}

# 创建目录
print_info "创建目录..."
mkdir -p "$INSTALL_BIN"
mkdir -p "$INSTALL_SHARE"
print_success "目录创建完成"

# 复制 te-cli 代码
print_info "安装 te-cli 到 $TE_INSTALL_DIR..."
rm -rf "$TE_INSTALL_DIR"
mkdir -p "$TE_INSTALL_DIR"
cp -rL "$REPO_DIR"/* "$TE_INSTALL_DIR/"
print_success "te-cli 安装完成"

# 创建包装脚本
print_info "创建包装脚本..."

cat > "$INSTALL_BIN/te" << 'EOF'
#!/bin/bash
TE_CLI_SHARE="${HOME}/.local/share/te-cli"

if [[ ! -d "$TE_CLI_SHARE" ]]; then
    echo "错误：te-cli 未正确安装"
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
print_success "包装脚本创建完成"

# 检查 PATH
if [[ ":$PATH:" != *":$INSTALL_BIN:"* ]]; then
    print_warning "$INSTALL_BIN 不在 PATH 中"
    echo "添加到 PATH："
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ te-cli 安装成功${NC}"
echo "=================================================="
echo ""
echo "安装位置："
echo "  - te 命令：$INSTALL_BIN/te"
echo "  - Python 代码：$TE_INSTALL_DIR/"
echo ""
echo "后续步骤："
echo "  1. 确保 $INSTALL_BIN 在 PATH 中"
echo "  2. 运行 'te --help' 进行配置"
echo ""
