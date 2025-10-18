# Scenario 5: 本地轻量级 RAG (Files-to-Prompt)

## 概述

基于 Simon Willison 的 [files-to-prompt](https://github.com/simonw/files-to-prompt) 理念，将代码库文件快速格式化为 LLM 提示词，实现本地轻量级 RAG。

## 核心功能

### 1. 快速上手代码库
几秒钟把关键源文件拼成一个大提示词，让 LLM 快速理解项目架构。

```bash
python cli.py rag \
    --patterns "**/*.py" "README.md" \
    --query "这个项目是怎么工作的？请概述架构和核心模块。" \
    --format xml \
    --cxml
```

### 2. 自动生成文档
从测试用例或源码自动生成 API 文档和使用说明。

```bash
python cli.py rag \
    --patterns "tests/**/*.py" \
    --query "根据测试用例生成 API 使用文档和示例代码。" \
    --format markdown
```

### 3. 代码导航定位
快速定位功能实现位置，无需手动搜索。

```bash
python cli.py rag \
    --patterns "**/*.py" \
    --query "snapshot 和 rollback 功能在哪些文件中实现？列出关键函数。" \
    --line-numbers \
    --cxml
```

### 4. 代码审阅分析
对特定模块进行质量审阅和改进建议。

```bash
python cli.py rag \
    --patterns "nodes/common/*.py" \
    --query "审阅代码质量，关注错误处理、代码复用和文档注释。" \
    --format xml
```

## 命令参数

### 必需参数
- `--query`: 要问 LLM 的问题

### 可选参数
- `--patterns`: 文件匹配模式（可多次指定，默认 `**/*.py`）
- `--format`: 输出格式 (`xml` 或 `markdown`，默认 `xml`)
- `--cxml`: 使用紧凑 XML 格式，适合长上下文模型（推荐）
- `--line-numbers`: 包含行号，便于精确定位代码
- `--model`: LLM 模型（默认 `claude-3-haiku-20240307`）

## 输出格式

### XML 格式（推荐用于长上下文）

标准 XML:
```xml
<documents>
<document>
<path>nodes/common/get_files_node.py</path>
<content>
from engine import node
...
</content>
</document>
</documents>
```

紧凑 XML (`--cxml`):
```xml
<documents><document path="nodes/common/get_files_node.py">from engine import node
...</document></documents>
```

### Markdown 格式

```markdown
## File: `nodes/common/get_files_node.py`

```python
from engine import node
...
```
```

## 使用示例

### 示例 1: 项目快速上手
```bash
python cli.py rag \
    --patterns "**/*.py" "README.md" \
    --query "这个项目的 Flow/Node 架构是如何工作的？" \
    --cxml
```

### 示例 2: 生成测试文档
```bash
python cli.py rag \
    --patterns "tests/**/*.py" \
    --query "根据测试用例，生成完整的 API 文档，包括参数、返回值和示例。" \
    --format markdown
```

### 示例 3: 功能定位
```bash
python cli.py rag \
    --patterns "nodes/**/*.py" \
    --query "LLM 调用功能在哪个文件？它支持哪些参数？" \
    --line-numbers
```

### 示例 4: 多模式匹配
```bash
python cli.py rag \
    --patterns "**/*.py" \
    --patterns "**/*.md" \
    --query "总结项目文档和代码中提到的四个核心场景。"
```

## 编程方式使用

```python
from scenarios.scenario_5_local_rag import run_rag_query

# 快速查询
result = run_rag_query(
    project_root=".",
    patterns=["**/*.py"],
    query="这个项目是如何工作的？",
    model="claude-3-haiku-20240307",
    format="xml",
    cxml=True
)

print("LLM 回答:", result.get('llm_response'))
print("处理文件数:", result.get('files_to_prompt_stats', {}).get('files_processed'))
```

### 预设场景函数

```python
from scenarios.scenario_5_local_rag import (
    quick_start_overview,
    generate_docs_from_tests,
    locate_feature,
    code_review_analysis
)

# 1. 项目概览
result = quick_start_overview(project_root=".")

# 2. 从测试生成文档
result = generate_docs_from_tests(project_root=".")

# 3. 定位功能
result = locate_feature(
    project_root=".",
    feature_query="JWT 校验功能"
)

# 4. 代码审阅
result = code_review_analysis(
    project_root=".",
    focus_area="错误处理和代码复用"
)
```

## Node 层面使用

```python
from engine import flow
from nodes.common import get_files_node, files_to_prompt_node, call_llm_node

# 创建自定义 Flow
f = flow()

# 步骤 1: 获取文件
f.add(get_files_node(), name="get_files", params={
    "patterns": ["**/*.py"],
    "exclude": ["**/__pycache__/**"]
})

# 步骤 2: 格式化为提示词
f.add(files_to_prompt_node(), name="format", params={
    "format": "xml",
    "cxml": True,
    "include_line_numbers": False
})

# 步骤 3: 调用 LLM
f.add(call_llm_node(), name="llm", params={
    "prompt_file": "prompts/rag_query.prompt.md",
    "model": "claude-3-haiku-20240307"
})

# 运行
result = f.run({"project_root": ".", "query": "你的问题"})
print(result.get("llm_response"))
```

## 最佳实践

### 1. 选择合适的格式
- **长上下文场景**: 使用 `--format xml --cxml`（紧凑，节省 token）
- **可读性优先**: 使用 `--format markdown`
- **精确定位**: 添加 `--line-numbers`

### 2. 优化文件匹配模式
```bash
# 只分析核心模块
--patterns "nodes/**/*.py" "scenarios/**/*.py"

# 排除测试和生成文件
--patterns "**/*.py" --exclude "tests/**" "**/*_pb2.py"

# 特定文件类型
--patterns "**/*.py" "**/*.md" "**/*.yaml"
```

### 3. 提示词优化
- **具体明确**: "列出所有 Node 类型及其功能" 优于 "介绍一下"
- **引导格式**: "以表格形式列出..." / "生成 Markdown 文档..."
- **上下文提示**: "根据测试用例..." / "参考 README..."

### 4. 性能优化
- 大型项目使用精确的 `--patterns` 避免处理无关文件
- 使用 `--cxml` 减少 token 消耗
- 针对特定问题缩小文件范围

## 演示脚本

运行完整演示：
```bash
bash examples/demo_scenario5_local_rag.sh
```

## 与 files-to-prompt 的对比

| 特性 | files-to-prompt | Scenario 5 RAG |
|------|----------------|----------------|
| 格式化文件 | 支持 | 支持 |
| XML/Markdown | 支持 | 支持 |
| 紧凑 XML (cxml) | 支持 | 支持 |
| 行号 | 支持 | 支持 |
| LLM 集成 | 需手动 | 自动集成 |
| Flow 编排 | 不支持 | 支持 |
| 统计信息 | 基础 | 详细 |
| 可扩展性 | 命令行工具 | Node 插件化 |

## 常见问题

### Q: 如何处理大型代码库？
A: 使用更精确的 `--patterns` 和 `--cxml` 压缩输出，或者分批查询不同模块。

### Q: 支持哪些文件类型？
A: 所有文本文件，通过 `--patterns` 指定，如 `*.py`, `*.js`, `*.md`, `*.yaml` 等。

### Q: 如何自定义提示词模板？
A: 修改 `prompts/rag_query.prompt.md` 或创建新的模板文件。

### Q: 输出可以保存到文件吗？
A: 可以通过重定向：`python cli.py rag ... > output.txt`

## 参考资源

- [files-to-prompt GitHub](https://github.com/simonw/files-to-prompt)
- [Simon Willison's Blog](https://simonwillison.net/)
- [LLM CLI Tool](https://llm.datasette.io/)
