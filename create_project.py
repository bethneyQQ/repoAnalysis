# -*- coding: utf-8 -*-
"""
项目结构生成脚本
运行: python create_project.py
"""
import os
import textwrap
from datetime import datetime


def create_file(path, content):
    """创建文件并写入内容"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).strip() + "\n")
    print(f"✅ Created: {path}")


def safe_timestamp():
    """文件系统安全的时间戳"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create_project_structure():
    """创建完整的项目结构"""

    # ============================================
    # 1) 项目根目录文件
    # ============================================

    # README.md
    create_file(
        "README.md",
        """
    # 代码仓库分析系统

    基于可插拔 Flow/Node 的代码仓库分析框架

    ## 特性
    - 🎯 Common vs Custom Nodes 清晰分离
    - 📦 Scenario 真正可插拔
    - 🚀 支持并行/异步（引擎可后续扩展）
    - 📊 可输出报告与指标

    ## 快速开始
    ```bash
    # 安装依赖
    pip install -r requirements.txt

    # 生成本地快照（示例）
    python cli.py snapshot --patterns "**/*.py"

    # 分析开源项目（占位）
    python cli.py adapt https://github.com/example/repo

    # 回归测试（占位）
    python cli.py test

    # 扫描架构漂移（占位）
    python cli.py drift --history-limit 100
    ```

    ## 项目结构
    ```
    repo-analysis/
    ├── nodes/                # Node 定义
    │   ├── common/           # 通用节点
    │   └── custom/           # 企业定制节点
    ├── scenarios/            # 场景定义
    ├── utils/                # 工具函数
    ├── configs/              # 配置文件
    ├── templates/            # 报告模板
    ├── docs/                 # 文档
    ├── tests/                # 单元测试
    └── cli.py                # CLI 入口
    ```
    """,
    )

    # requirements.txt（已移除 pocketflow）
    create_file(
        "requirements.txt",
        """
    click>=8.0.0
    pyyaml>=6.0.0
    requests>=2.28.0
    gitpython>=3.1.0
    tree-sitter>=0.20.0
    jinja2>=3.1.0
    """,
    )

    # setup.py
    create_file(
        "setup.py",
        """
    from setuptools import setup, find_packages

    setup(
        name="repo-analysis",
        version="1.0.0",
        description="Pluggable repository analysis framework",
        author="Your Name",
        packages=find_packages(),
        install_requires=[
            "click>=8.0.0",
            "pyyaml>=6.0.0",
            "requests>=2.28.0",
            "gitpython>=3.1.0",
        ],
        entry_points={
            "console_scripts": [
                "repo-analysis=cli:cli",
            ],
        },
    )
    """,
    )

    # .gitignore
    create_file(
        ".gitignore",
        """
    __pycache__/
    *.py[cod]
    *$py.class
    *.so
    .Python
    env/
    venv/
    .venv/
    .ai-snapshots/
    .quality-baseline.json
    reports/
    *.log
    .DS_Store
    """,
    )

    # ============================================
    # 2) 简化 Flow 引擎（极简内置，不创建 pocketflow 目录）
    #    仅供 demo；后续可替换为成熟引擎
    # ============================================
    create_file(
        "engine.py",
        """
    # 极简 Flow 引擎（仅演示串行执行，on/post/condition 未实现）
    def node(prep=None, exec=None, post=None):
        return {
            "prep": prep or (lambda ctx, params: {}),
            "exec": exec or (lambda prep_result, params: prep_result),
            "post": post or (lambda ctx, prep_result, exec_result, params: "next")
        }

    class Flow:
        def __init__(self):
            self.nodes = []

        def add(self, node_func, name, on=None, params=None):
            self.nodes.append({
                "name": name,
                "node": node_func,
                "on": on,
                "params": params or {}
            })
            return self

        def run(self, shared_store):
            for nfo in self.nodes:
                n = nfo["node"]
                p = nfo["params"]
                prep = n["prep"](shared_store, p)
                out = n["exec"](prep, p)
                _ = n["post"](shared_store, prep, out, p)
            return shared_store

    def flow():
        return Flow()
    """,
    )

    # ============================================
    # 3) Common Nodes
    # ============================================
    create_file("nodes/__init__.py", "")
    create_file("nodes/common/__init__.py", "")

    # GetFilesNode
    create_file(
        "nodes/common/get_files_node.py",
        """
    from engine import node
    from pathlib import Path
    import fnmatch

    def get_files_node():
        \"\"\"获取文件列表节点\"\"\"        
        def prep(ctx, params):
            project_root = Path(ctx.get("project_root", ".")).resolve()
            patterns = params.get("patterns", ["**/*"])
            exclude = params.get("exclude", ["node_modules/**", ".git/**", "__pycache__/**"])
            extensions = params.get("extensions", [])
            return {
                "project_root": project_root,
                "patterns": patterns,
                "exclude": exclude,
                "extensions": extensions
            }

        def exec(prep_result, params):
            root = prep_result["project_root"]
            patterns = prep_result["patterns"]
            exclude = prep_result["exclude"]
            exts = prep_result["extensions"]

            all_files = []
            for path in root.glob("**/*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(root).as_posix()

                # include
                if not any(fnmatch.fnmatch(rel, pat) for pat in patterns):
                    continue
                # exclude
                if any(fnmatch.fnmatch(rel, ex) for ex in exclude):
                    continue
                # extension
                if exts and path.suffix not in exts:
                    continue

                all_files.append(str(path.resolve()))
            return all_files

        def post(ctx, prep_result, exec_result, params):
            ctx["files"] = exec_result
            ctx["file_count"] = len(exec_result)
            return "files_retrieved"

        return node(prep=prep, exec=exec, post=post)
    """,
    )

    # ParseCodeNode
    create_file(
        "nodes/common/parse_code_node.py",
        """
    from engine import node
    from utils.ast_parser import parse_file

    def parse_code_node():
        \"\"\"解析代码生成 AST 节点\"\"\"
        def prep(ctx, params):
            files = ctx.get("files", [])
            language = params.get("language", "auto")
            return {"files": files, "language": language}

        def exec(prep_result, params):
            ast_results = []
            for fp in prep_result["files"]:
                try:
                    ast_obj = parse_file(fp, prep_result["language"])
                    ast_results.append({"path": fp, "ast": ast_obj, "success": True})
                except Exception as e:
                    ast_results.append({"path": fp, "error": str(e), "success": False})
            return ast_results

        def post(ctx, prep_result, exec_result, params):
            ctx["ast_results"] = exec_result
            ctx["parsed_file_count"] = sum(1 for r in exec_result if r["success"])
            return "parse_complete" if ctx["parsed_file_count"] > 0 else "parse_failed"

        return node(prep=prep, exec=exec, post=post)
    """,
    )

    # CallLLMNode
    create_file(
        "nodes/common/call_llm_node.py",
        """
    from engine import node
    from utils.llm_client import call_llm

    def call_llm_node():
        \"\"\"调用 LLM 节点\"\"\"
        def prep(ctx, params):
            template = params.get("prompt_template", "")
            # 防止 KeyError：允许模板里出现缺失字段
            class D(dict):
                def __missing__(self, k): return ""
            prompt = template.format_map(D(**ctx))
            return {
                "prompt": prompt,
                "model": params.get("model", "gpt-4"),
                "temperature": params.get("temperature", 0.2),
                "max_tokens": params.get("max_tokens", 2000)
            }

        def exec(prep_result, params):
            try:
                resp = call_llm(
                    prompt=prep_result["prompt"],
                    model=prep_result["model"],
                    temperature=prep_result["temperature"],
                    max_tokens=prep_result["max_tokens"]
                )
                return {"success": True, "response": resp}
            except Exception as e:
                return {"success": False, "error": str(e)}

        def post(ctx, prep_result, exec_result, params):
            if exec_result["success"]:
                ctx["llm_response"] = exec_result["response"]
                return "llm_complete"
            ctx["llm_error"] = exec_result["error"]
            return "llm_failed"

        return node(prep=prep, exec=exec, post=post)
    """,
    )

    # WriteFileNode
    create_file(
        "nodes/common/write_file_node.py",
        f"""
    from engine import node
    import json, os

    def _safe_ts():
        return "{safe_timestamp()}"

    def write_file_node():
        \"\"\"写入文件节点\"\"\"
        def prep(ctx, params):
            output_path = params.get("output_path", "output.json")
            output_path = output_path.replace("{{timestamp}}", _safe_ts())
            data_key = params.get("data_key", "data")
            data = ctx.get(data_key, ctx)
            return {{"output_path": output_path, "format": params.get("format", "json"), "data": data}}

        def exec(prep_result, params):
            try:
                os.makedirs(os.path.dirname(prep_result["output_path"]) or ".", exist_ok=True)
                with open(prep_result["output_path"], "w", encoding="utf-8") as f:
                    if prep_result["format"] == "json":
                        json.dump(prep_result["data"], f, indent=2, ensure_ascii=False, default=str)
                    else:
                        f.write(str(prep_result["data"]))
                return {{"success": True, "path": prep_result["output_path"]}}
            except Exception as e:
                return {{"success": False, "error": str(e)}}

        def post(ctx, prep_result, exec_result, params):
            if exec_result["success"]:
                ctx["output_file_path"] = exec_result["path"]
                return "file_written"
            ctx["write_error"] = exec_result["error"]
            return "write_failed"

        return node(prep=prep, exec=exec, post=post)
    """,
    )

    # ============================================
    # 4) Custom Nodes
    # ============================================
    create_file("nodes/custom/__init__.py", "")

    create_file(
        "nodes/custom/check_naming_convention_node.py",
        """
    from engine import node
    from utils.naming_checker import check_naming_convention

    def check_naming_convention_node():
        \"\"\"检查命名规范节点\"\"\"
        def prep(ctx, params):
            ast_results = ctx.get("ast_results", [])
            rules = params.get("naming_rules", {
                "file": "kebab-case",
                "class": "PascalCase",
                "function": "camelCase",
                "constant": "UPPER_SNAKE_CASE"
            })
            return {"ast_results": ast_results, "rules": rules}

        def exec(prep_result, params):
            vs = []
            for item in prep_result["ast_results"]:
                if not item.get("success"):
                    continue
                file_v = check_naming_convention(item["ast"], prep_result["rules"])
                if file_v:
                    vs.append({"file": item["path"], "violations": file_v})
            return vs

        def post(ctx, prep_result, exec_result, params):
            ctx["naming_violations"] = exec_result
            ctx["naming_violation_count"] = sum(len(v["violations"]) for v in exec_result)
            return "has_violations" if exec_result else "all_passed"

        return node(prep=prep, exec=exec, post=post)
    """,
    )

    # ============================================
    # 5) Utils
    # ============================================
    create_file("utils/__init__.py", "")

    create_file(
        "utils/ast_parser.py",
        """
    import ast
    from pathlib import Path

    def parse_file(file_path, language='auto'):
        if language == 'auto':
            language = detect_language(file_path)
        if language == 'python':
            return parse_python(file_path)
        raise NotImplementedError(f"Language {language} not supported yet")

    def detect_language(file_path):
        suffix = Path(file_path).suffix
        language_map = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.java': 'java'}
        return language_map.get(suffix, 'unknown')

    def parse_python(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        return ast.parse(code, filename=file_path)
    """,
    )

    create_file(
        "utils/llm_client.py",
        """
    import os
    def call_llm(prompt, model='gpt-4', temperature=0.2, max_tokens=2000):
        # 示例：如果未配置 API Key，则返回 mock
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return f"[Mock LLM Response] {prompt[:100]}..."
        # TODO: 集成真实 LLM 调用
        return f"[Mock LLM Response] {prompt[:100]}..."
    """,
    )

    create_file(
        "utils/naming_checker.py",
        """
    import re
    import ast

    def check_naming_convention(ast_tree, rules):
        violations = []
        # 类名
        if 'class' in rules:
            for node in ast.walk(ast_tree):
                if isinstance(node, ast.ClassDef):
                    if not matches_convention(node.name, rules['class']):
                        violations.append({'type':'class','name':node.name,'line':node.lineno,'expected':rules['class']})
        # 函数名
        if 'function' in rules:
            for node in ast.walk(ast_tree):
                if isinstance(node, ast.FunctionDef):
                    if not matches_convention(node.name, rules['function']):
                        violations.append({'type':'function','name':node.name,'line':node.lineno,'expected':rules['function']})
        return violations

    def matches_convention(name, convention):
        patterns = {
            'kebab-case': r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$',
            'snake_case': r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$',
            'camelCase': r'^[a-z][a-zA-Z0-9]*$',
            'PascalCase': r'^[A-Z][a-zA-Z0-9]*$',
            'UPPER_SNAKE_CASE': r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$',
        }
        pattern = patterns.get(convention)
        if not pattern:
            return True
        return bool(re.match(pattern, name))
    """,
    )

    # ============================================
    # 6) Scenarios
    # ============================================
    create_file("scenarios/__init__.py", "")

    create_file(
        "scenarios/scenario_1_local_snapshot.py",
        """
    from engine import flow
    from nodes.common.get_files_node import get_files_node
    from nodes.common.parse_code_node import parse_code_node
    from nodes.common.call_llm_node import call_llm_node
    from nodes.common.write_file_node import write_file_node

    def create_local_snapshot_scenario(config):
        f = flow()
        f.add(get_files_node(), name="get_files", params={
            "patterns": config.get("file_patterns", ["**/*.py"]),
            "exclude": [".git/**", "__pycache__/**", ".ai-snapshots/**"]
        })
        f.add(parse_code_node(), name="parse_code", params={"language": "python"})
        f.add(call_llm_node(), name="ai_analyze", params={
            "prompt_template": '''
            分析以下代码结构并提出改进建议：
            文件数量：{file_count}
            成功解析：{parsed_file_count}
            输出 1) 质量评估 2) 改进建议 3) 潜在风险点
            ''',
            "model": "gpt-4"
        })
        f.add(write_file_node(), name="save_snapshot", params={
            "output_path": ".ai-snapshots/snapshot-{timestamp}.json",
            "format": "json",
            "data_key": "llm_response"
        })
        return f

    def run(config=None):
        config = config or {"file_patterns": ["**/*.py"]}
        scenario = create_local_snapshot_scenario(config)
        shared_store = {"project_root": ".", "timestamp": "AUTO"}
        result = scenario.run(shared_store)
        return result
    """,
    )

    # ============================================
    # 7) CLI（新增 adapt / drift 占位命令）
    # ============================================
    create_file(
        "cli.py",
        """
    import click
    from scenarios import scenario_1_local_snapshot

    @click.group()
    def cli():
        \"\"\"代码仓库分析工具\"\"\"
        pass

    @cli.command()
    @click.option('--patterns', multiple=True, default=['**/*.py'], help='文件匹配模式')
    @click.option('--output', default='.ai-snapshots', help='输出目录（当前未直接使用）')
    def snapshot(patterns, output):
        \"\"\"创建本地快照\"\"\"
        config = {'file_patterns': list(patterns), 'output_dir': output}
        result = scenario_1_local_snapshot.run(config)
        out = result.get('output_file_path')
        if out:
            click.echo(f"✅ 快照已保存：{out}")
        else:
            click.echo("✅ 快照已生成（mock LLM 内容），详见 .ai-snapshots/ 目录")

    @cli.command()
    @click.argument('repo', required=False)
    def adapt(repo):
        \"\"\"开源项目理解与组织化改造（占位）\"\"\"
        click.echo("🔧 adapt: TBD（将根据 org_rules 与依赖图生成改造计划）")
        if repo:
            click.echo(f"   输入 repo: {repo}")

    @cli.command()
    @click.option('--history-limit', default=100, help='历史窗口大小')
    def drift(history_limit):
        \"\"\"架构漂移扫描（占位）\"\"\"
        click.echo(f"🏗️  drift: TBD（history_limit={history_limit}）")

    @cli.command()
    def test():
        \"\"\"回归测试（占位）\"\"\"
        click.echo("🧪 运行测试... (TBD)")
        click.echo("✅ 占位完成")

    if __name__ == '__main__':
        cli()
    """,
    )

    # ============================================
    # 8) Configs / Docs / Templates / Examples
    # ============================================
    create_file(
        "configs/org_standards.yaml",
        """
    naming:
      file: kebab-case
      class: PascalCase
      function: camelCase
      constant: UPPER_SNAKE_CASE
    """,
    )

    create_file(
        "configs/node_registry.yaml",
        """
    # Node 注册表（工厂函数方式）
    common_nodes:
      - id: get_files
        module: nodes.common.get_files_node
        factory: get_files_node
      - id: parse_code
        module: nodes.common.parse_code_node
        factory: parse_code_node
    custom_nodes:
      - id: check_naming
        module: nodes.custom.check_naming_convention_node
        factory: check_naming_convention_node
    """,
    )

    # docs skeleton
    create_file("docs/architecture.md", "# 架构设计\n")
    create_file("docs/node-development.md", "# Node 开发指南\n")
    create_file("docs/scenario-development.md", "# Scenario 开发指南\n")

    # dirs
    os.makedirs("templates", exist_ok=True)
    os.makedirs("examples", exist_ok=True)

    # ============================================
    # 9) Tests
    # ============================================
    create_file("tests/__init__.py", "")
    create_file(
        "tests/test_nodes.py",
        """
    import unittest
    from nodes.common.get_files_node import get_files_node

    class TestGetFilesNode(unittest.TestCase):
        def test_get_files(self):
            n = get_files_node()
            ctx = {'project_root': '.'}
            params = {'patterns': ['*.py']}
            prep = n['prep'](ctx, params)
            result = n['exec'](prep, params)
            self.assertIsInstance(result, list)

    if __name__ == '__main__':
        unittest.main()
    """,
    )


if __name__ == "__main__":
    create_project_structure()
    print("🎉 Project structure generated.")
