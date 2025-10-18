#!/usr/bin/env bash
# 场景①：本地快照实验

set -euo pipefail
source "$(dirname "$0")/common.sh"

echo "================================================"
echo "场景①：本地快照与回滚"
echo "================================================"

# 运行快照命令
$PYTHON cli.py snapshot --patterns "**/*.py" | tee /tmp/snap.out

# 检查输出
if grep -E "snapshot|快照|.ai-snapshots" /tmp/snap.out >/dev/null; then
    ok "快照生成成功"
else
    warn "输出里没找到快照提示，但命令已执行"
fi

# 检查快照文件是否生成
if [ -d ".ai-snapshots" ]; then
    SNAP_COUNT=$(find .ai-snapshots -name "snapshot-*.md" 2>/dev/null | wc -l)
    if [ "$SNAP_COUNT" -gt 0 ]; then
        ok "找到 $SNAP_COUNT 个快照文件"
        # 显示最新的快照文件
        LATEST=$(find .ai-snapshots -name "snapshot-*.md" 2>/dev/null | sort -r | head -1)
        if [ -n "$LATEST" ]; then
            echo ""
            echo "📄 最新快照: $LATEST"
            echo "--- 前20行 ---"
            head -20 "$LATEST"
            echo "--- (省略) ---"
        fi
    fi
fi

ok "场景① 实验完成"
