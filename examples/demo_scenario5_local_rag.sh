#!/bin/bash
# Demo: Scenario 5 - Local RAG (Files-to-Prompt)

set -e

echo "=========================================="
echo "Scenario 5: Local RAG 演示"
echo "=========================================="
echo ""

# 场景 1: 快速上手 - 项目概览
echo ">>> 场景 1: 快速上手整个代码库"
echo ">>> 问题: '这个项目是怎么工作的？'"
echo ""
python cli.py rag \
    --patterns "**/*.py" "README.md" \
    --query "这个项目是怎么工作的？请概述项目架构、Flow/Node 机制和四个核心场景。" \
    --format xml \
    --cxml \
    --model "claude-3-haiku-20240307"

echo ""
echo "=========================================="
echo ""

# 场景 2: 从测试生成文档
echo ">>> 场景 2: 从测试用例生成 API 文档"
echo ""
python cli.py rag \
    --patterns "tests/**/*.py" \
    --query "根据测试用例，生成这个项目的 API 使用文档，包括主要的 Node 类型和使用示例。" \
    --format markdown \
    --model "claude-3-haiku-20240307"

echo ""
echo "=========================================="
echo ""

# 场景 3: 定位功能实现
echo ">>> 场景 3: 定位功能实现"
echo ">>> 查找: 'snapshot 和 rollback 功能'"
echo ""
python cli.py rag \
    --patterns "**/*.py" \
    --query "snapshot（快照）和 rollback（回滚）功能在哪些文件中实现？请列出关键函数和它们的功能。" \
    --format xml \
    --cxml \
    --line-numbers \
    --model "claude-3-haiku-20240307"

echo ""
echo "=========================================="
echo ""

# 场景 4: 代码审阅
echo ">>> 场景 4: 代码质量审阅"
echo ""
python cli.py rag \
    --patterns "nodes/common/*.py" \
    --query "审阅 common nodes 的代码质量，关注：1) 错误处理 2) 代码复用 3) 文档注释。给出改进建议。" \
    --format xml \
    --model "claude-3-haiku-20240307"

echo ""
echo "=========================================="
echo "演示完成！"
echo ""
echo "其他用法示例："
echo "  python cli.py rag --patterns '**/*.py' --query '你的问题' --format xml"
echo "  python cli.py rag --patterns 'tests/**' --query '生成文档' --format markdown"
echo "=========================================="
