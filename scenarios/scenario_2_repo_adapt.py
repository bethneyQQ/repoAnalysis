"""
场景②：开源项目理解与组织化改造 (Repo Adaptation)

工作流：
1. CloneRepo: 克隆仓库到临时目录
2. AnalyzeRepo: 分析目录结构、依赖图、入口点
3. LoadOrgRules: 加载组织规范
4. LLMAdapt: AI 生成适配计划
5. SavePlan: 保存改造计划
"""

from engine import flow
from nodes.common.call_llm_node import call_llm_node
from nodes.common.write_file_node import write_file_node
from pathlib import Path
import subprocess
import tempfile
import shutil
import yaml


def create_repo_adapt_scenario(config):
    """创建开源仓库适配场景"""
    f = flow()

    # 1. 克隆仓库（简化版，实际应作为独立 Node）
    def clone_repo_prep(ctx, params):
        repo_url = params.get("repo_url", ctx.get("repo_url", ""))
        temp_dir = tempfile.mkdtemp(prefix="repo_adapt_")
        return {"repo_url": repo_url, "temp_dir": temp_dir}

    def clone_repo_exec(prep_result, params):
        try:
            result = subprocess.run(
                ["git", "clone", "--depth=1", prep_result["repo_url"], prep_result["temp_dir"]],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return {"success": True, "path": prep_result["temp_dir"]}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clone_repo_post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["repo_path"] = exec_result["path"]
            ctx["repo_url"] = prep_result["repo_url"]
            return "cloned"
        ctx["clone_error"] = exec_result["error"]
        return "clone_failed"

    from engine import node
    clone_node = node(prep=clone_repo_prep, exec=clone_repo_exec, post=clone_repo_post)
    f.add(clone_node, name="clone_repo", params={"repo_url": config.get("repo_url", "")})

    # 2. 分析仓库（简化版）
    def analyze_repo_prep(ctx, params):
        repo_path = Path(ctx.get("repo_path", "."))
        return {"repo_path": repo_path}

    def analyze_repo_exec(prep_result, params):
        repo_path = prep_result["repo_path"]

        # 生成目录摘要
        try:
            tree_result = subprocess.run(
                ["tree", "-L", "3", "-I", "__pycache__|*.pyc|.git", str(repo_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            repo_tree = tree_result.stdout if tree_result.returncode == 0 else "N/A"
        except:
            repo_tree = "N/A"

        # 检测语言和构建系统
        language = "unknown"
        build_system = "unknown"
        if (repo_path / "setup.py").exists() or (repo_path / "pyproject.toml").exists():
            language = "python"
            build_system = "setuptools" if (repo_path / "setup.py").exists() else "poetry"
        elif (repo_path / "package.json").exists():
            language = "javascript"
            build_system = "npm"

        # 查找入口点（简化）
        entry_points = []
        for pattern in ["main.py", "cli.py", "app.py", "__main__.py"]:
            matches = list(repo_path.rglob(pattern))
            entry_points.extend([str(p.relative_to(repo_path)) for p in matches[:5]])

        return {
            "repo_tree": repo_tree[:2000],  # 限制长度
            "language": language,
            "build_system": build_system,
            "entry_points": entry_points[:10],
            "dep_graph_summary": "暂未实现，需集成依赖分析工具"
        }

    def analyze_repo_post(ctx, prep_result, exec_result, params):
        ctx.update(exec_result)
        return "analyzed"

    analyze_node = node(prep=analyze_repo_prep, exec=analyze_repo_exec, post=analyze_repo_post)
    f.add(analyze_node, name="analyze_repo")

    # 3. 加载组织规范
    def load_org_rules_prep(ctx, params):
        rules_path = Path(params.get("org_rules_path", "docs/org_rules.yaml"))
        return {"rules_path": rules_path}

    def load_org_rules_exec(prep_result, params):
        rules_path = prep_result["rules_path"]
        if rules_path.exists():
            with open(rules_path, "r", encoding="utf-8") as f:
                rules = yaml.safe_load(f)
            summary = yaml.dump(rules, default_flow_style=False, allow_unicode=True)
            return {"success": True, "summary": summary[:1000]}
        return {"success": True, "summary": "无组织规范文件"}

    def load_org_rules_post(ctx, prep_result, exec_result, params):
        ctx["org_rules_summary"] = exec_result["summary"]
        return "rules_loaded"

    load_rules_node = node(prep=load_org_rules_prep, exec=load_org_rules_exec, post=load_org_rules_post)
    f.add(load_rules_node, name="load_org_rules")

    # 4. LLM 生成适配计划
    f.add(call_llm_node(), name="llm_adapt", params={
        "prompt_file": "prompts/repo_adapt.prompt.md",
        "model": config.get("model", "gpt-4"),
        "temperature": 0.2,
        "max_tokens": 3000
    })

    # 5. 保存计划
    f.add(write_file_node(), name="save_plan", params={
        "output_path": ".ai-snapshots/repo_adapt_plan-{timestamp}.md",
        "format": "text",
        "data_key": "llm_response"
    })

    return f


def run(config=None):
    """运行场景②"""
    config = config or {}
    if not config.get("repo_url"):
        print("WARNING: 需要提供 repo_url 参数")
        return {"error": "missing repo_url"}

    scenario = create_repo_adapt_scenario(config)
    shared_store = {"project_root": ".", "timestamp": "AUTO"}

    try:
        result = scenario.run(shared_store)
        return result
    finally:
        # 清理临时目录
        if "repo_path" in shared_store:
            try:
                shutil.rmtree(shared_store["repo_path"])
            except:
                pass
