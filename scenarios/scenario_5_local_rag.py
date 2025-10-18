"""
Scenario 5: Local RAG - Files-to-Prompt 本地轻量级 RAG

核心用例：
1. 快速上手：几秒钟把关键源文件拼成一个大提示词，问"这个项目是怎么工作的？"
2. 自动生成文档：从测试/源码生成 API 文档和概览
3. 代码导航：定位功能实现位置，如"JWT 校验在哪实现？"
4. 长上下文优化：支持 Claude XML 格式（--cxml）或 Markdown
"""

from engine import flow
from nodes.common import (
    get_files_node,
    files_to_prompt_node,
    call_llm_node
)


def create_local_rag_scenario(config):
    """创建本地 RAG 场景

    用法示例：
    1. 项目概览：patterns=["**/*.py"], query="这个项目是怎么工作的？"
    2. 生成文档：patterns=["tests/**/*.py"], query="根据测试用例生成 API 文档"
    3. 定位功能：patterns=["**/*.py"], query="JWT 校验在哪实现？"
    """
    f = flow()

    # 步骤 1: 获取文件列表
    f.add(
        get_files_node(),
        name="get_files",
        params={
            "patterns": config.get("patterns", ["**/*.py"]),
            "exclude": config.get("exclude", [
                "**/__pycache__/**",
                "**/.git/**",
                "**/.ai-snapshots/**",
                "**/node_modules/**",
                "**/*.pyc",
                "**/venv/**",
                "**/.venv/**"
            ])
        }
    )

    # 步骤 2: 格式化为 LLM 提示（files-to-prompt 风格）
    f.add(
        files_to_prompt_node(),
        name="format_files",
        params={
            "format": config.get("format", "xml"),  # xml 或 markdown
            "include_line_numbers": config.get("include_line_numbers", False),
            "cxml": config.get("cxml", True),  # 紧凑 XML，适合长上下文
            "include_stats": config.get("include_stats", True),
            "output_key": "formatted_prompt"
        }
    )

    # 步骤 3: 调用 LLM 回答问题
    f.add(
        call_llm_node(),
        name="llm_query",
        params={
            "prompt_file": config.get("prompt_file", "prompts/rag_query.prompt.md"),
            "model": config.get("model", "claude-3-haiku-20240307"),
            "temperature": config.get("temperature", 0.2),
            "max_tokens": config.get("max_tokens", 4000)
        }
    )

    return f


def run_rag_query(project_root=".", patterns=None, query="", model="claude-3-haiku-20240307", **kwargs):
    """运行 RAG 查询

    Examples:
        # 快速上手整个项目
        run_rag_query(query="这个项目的架构是什么？有哪些核心模块？")

        # 从测试生成文档
        run_rag_query(patterns=["tests/**/*.py"], query="根据测试用例生成 API 使用文档")

        # 定位功能实现
        run_rag_query(patterns=["**/*.py"], query="文件快照功能在哪个文件实现？")
    """
    if patterns is None:
        patterns = ["**/*.py"]

    config = {
        "project_root": project_root,
        "patterns": patterns,
        "query": query,
        "model": model,
        **kwargs
    }

    scenario = create_local_rag_scenario(config)

    # 初始化共享存储
    shared_store = {
        "project_root": project_root,
        "query": query
    }

    # 运行场景
    result = scenario.run(shared_store)

    return result


# ========== 预设场景 ==========

def quick_start_overview(project_root=".", model="claude-3-haiku-20240307"):
    """场景 1：快速上手 - 项目概览"""
    return run_rag_query(
        project_root=project_root,
        patterns=["**/*.py", "**/*.md"],
        query="这个项目是怎么工作的？请概述项目架构、核心模块和主要功能。",
        model=model,
        format="xml",
        cxml=True
    )


def generate_docs_from_tests(project_root=".", model="claude-3-haiku-20240307"):
    """场景 2：从测试生成文档"""
    return run_rag_query(
        project_root=project_root,
        patterns=["tests/**/*.py", "**/*_test.py"],
        query="根据测试用例，生成这个项目的 API 使用文档和示例代码。",
        model=model,
        format="markdown",
        include_line_numbers=True
    )


def locate_feature(project_root=".", feature_query="", model="claude-3-haiku-20240307"):
    """场景 3：定位功能实现"""
    return run_rag_query(
        project_root=project_root,
        patterns=["**/*.py"],
        query=f"在代码库中定位以下功能的实现位置：{feature_query}。请指出具体的文件和函数。",
        model=model,
        format="xml",
        cxml=True,
        include_line_numbers=True
    )


def code_review_analysis(project_root=".", focus_area="", model="claude-3-haiku-20240307"):
    """场景 4：代码审阅分析"""
    return run_rag_query(
        project_root=project_root,
        patterns=["**/*.py"],
        query=f"对以下方面进行代码审阅：{focus_area}。指出潜在问题和改进建议。",
        model=model,
        format="xml",
        cxml=True
    )


if __name__ == "__main__":
    import sys

    print("=" * 80)
    print("Scenario 5: Local RAG - Files-to-Prompt 本地轻量级 RAG")
    print("=" * 80)

    # 场景 1: 快速上手项目
    print("\n[场景 1] 快速上手 - 项目概览")
    print("-" * 80)
    result = quick_start_overview(project_root=".", model="claude-3-haiku-20240307")

    stats = result.get("files_to_prompt_stats", {})
    print(f"处理文件数: {stats.get('files_processed', 0)}")
    print(f"总行数: {stats.get('total_lines', 0)}")
    print(f"总字符数: {stats.get('total_chars', 0)}")
    print(f"\n问题: {result.get('query')}")
    print(f"\nLLM 回答:")
    print("-" * 80)
    print(result.get("llm_response", "No response"))

    # 场景 2: 定位功能（示例）
    if len(sys.argv) > 1:
        print("\n\n[场景 2] 定位功能实现")
        print("-" * 80)
        feature = " ".join(sys.argv[1:])
        result = locate_feature(project_root=".", feature_query=feature)
        print(f"问题: 定位功能 - {feature}")
        print(f"\nLLM 回答:")
        print("-" * 80)
        print(result.get("llm_response", "No response"))

    print("\n" + "=" * 80)
    print("提示：可以运行 'python scenarios/scenario_5_local_rag.py <功能查询>' 来定位功能")
    print("=" * 80)
