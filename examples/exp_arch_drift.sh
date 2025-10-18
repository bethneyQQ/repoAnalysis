#!/usr/bin/env bash
# 场景④：架构影响与漂移扫描实验

set -euo pipefail
source "$(dirname "$0")/common.sh"

echo "================================================"
echo "场景④：架构影响与漂移扫描"
echo "================================================"

# 运行架构漂移扫描命令
$PYTHON cli.py arch-drift | tee /tmp/drift.out

# 检查输出
if grep -E "arch_gate:|score:|架构" /tmp/drift.out >/dev/null; then
    ok "架构门禁结果已输出"

    # 判断是否通过
    if grep -E "pass.*true|PASS|通过" /tmp/drift.out >/dev/null; then
        ok "✅ 架构门禁通过"
    elif grep -E "pass.*false|FAIL|失败" /tmp/drift.out >/dev/null; then
        warn "❌ 架构门禁失败"
    fi
elif grep -E "✅|已保存" /tmp/drift.out >/dev/null; then
    ok "命令执行成功"
else
    warn "命令已执行，请检查输出"
fi

# 检查架构门禁文件
if [ -d ".ai-snapshots" ]; then
    ARCH_COUNT=$(find .ai-snapshots -name "arch_gate-*.md" 2>/dev/null | wc -l)
    if [ "$ARCH_COUNT" -gt 0 ]; then
        ok "找到 $ARCH_COUNT 个架构门禁文件"
        # 显示最新的架构门禁文件
        LATEST=$(find .ai-snapshots -name "arch_gate-*.md" 2>/dev/null | sort -r | head -1)
        if [ -n "$LATEST" ]; then
            echo ""
            echo "📐 最新架构门禁: $LATEST"
            echo "--- 内容 ---"
            cat "$LATEST"
            echo "--- (完) ---"
        fi
    fi
fi

ok "场景④ 实验完成"
