#!/usr/bin/env bash
# 一键运行所有实验场景

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "🚀 运行所有实验场景"
echo "========================================"
echo ""

# 场景①：本地快照
bash "$SCRIPT_DIR/exp_snapshot.sh"
echo ""

# 场景②：开源项目改造（可选，因为需要克隆仓库较慢）
read -p "是否运行场景②（需要克隆 Git 仓库，较慢）？[y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    bash "$SCRIPT_DIR/exp_repo_adapt.sh"
    echo ""
else
    echo "⏭️  跳过场景②"
    echo ""
fi

# 场景③：回归检测
bash "$SCRIPT_DIR/exp_regression.sh"
echo ""

# 场景④：架构漂移
bash "$SCRIPT_DIR/exp_arch_drift.sh"
echo ""

echo "========================================"
echo "🎉 所有实验场景执行完毕"
echo "========================================"
echo ""
echo "📂 查看生成的文件："
echo "   ls -lh .ai-snapshots/"
echo ""
