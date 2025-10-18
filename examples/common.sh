#!/usr/bin/env bash
# 通用辅助函数

set -euo pipefail

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 辅助函数
ok() {
    echo -e "${GREEN}✔ $*${NC}"
}

fail() {
    echo -e "${RED}✘ $*${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}⚠ $*${NC}"
}

# 检查是否在项目根目录
[ -f "cli.py" ] || fail "请在项目根目录执行（未找到 cli.py）"

# 检查 Python
command -v python >/dev/null || command -v python3 >/dev/null || fail "需要 python 或 python3"

# 使用 python3 如果可用
if command -v python3 >/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

export PYTHON
