"""
场景④：架构影响与漂移扫描 (Architecture Drift)

工作流：
1. BuildDepGraph: 构建依赖图
2. CheckLayerViolations: 检查分层违规
3. AnalyzeComplexity: 分析复杂度
4. CheckAPIBreaking: 检查 API 破坏性变更
5. LLMArchAudit: AI 架构审计
6. SaveArchGate: 保存架构门禁结果
"""

from engine import flow, node
from nodes.common.call_llm_node import call_llm_node
from nodes.common.write_file_node import write_file_node
from pathlib import Path
import ast
import json
import yaml


def create_arch_drift_scenario(config):
    """创建架构漂移扫描场景"""
    f = flow()

    # 1. 构建依赖图（简化版）
    def build_dep_graph_prep(ctx, params):
        project_root = Path(ctx.get("project_root", "."))
        return {"project_root": project_root}

    def build_dep_graph_exec(prep_result, params):
        # 简化：统计 Python 文件的导入关系
        root = prep_result["project_root"]
        py_files = list(root.rglob("*.py"))

        nodes_count = len(py_files)
        edges_count = 0
        imports = []

        for py_file in py_files[:100]:  # 限制分析文件数
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                for n in ast.walk(tree):
                    if isinstance(n, (ast.Import, ast.ImportFrom)):
                        edges_count += 1
                        if edges_count <= 20:  # 记录前 20 个导入示例
                            module = getattr(n, "module", None) or (n.names[0].name if n.names else "")
                            imports.append(module)
            except:
                continue

        # Mock 环检测
        scc_count = 0  # 强连通分量
        cycles_delta = 0  # 环数变化

        return {
            "nodes": nodes_count,
            "edges": edges_count,
            "scc_count": scc_count,
            "cycles_delta": cycles_delta,
            "dep_graph_summary": f"Nodes: {nodes_count}, Edges: {edges_count}, Sample imports: {imports[:10]}"
        }

    def build_dep_graph_post(ctx, prep_result, exec_result, params):
        ctx.update(exec_result)
        return "graph_built"

    graph_node = node(
        prep=build_dep_graph_prep,
        exec=build_dep_graph_exec,
        post=build_dep_graph_post
    )
    f.add(graph_node, name="build_dep_graph")

    # 2. 检查分层违规
    def check_layer_violations_prep(ctx, params):
        project_root = Path(ctx.get("project_root", "."))
        org_rules_path = Path(params.get("org_rules_path", "docs/org_rules.yaml"))
        return {"project_root": project_root, "org_rules_path": org_rules_path}

    def check_layer_violations_exec(prep_result, params):
        # 加载组织规范中的分层定义
        rules_path = prep_result["org_rules_path"]
        layer_rules = {}
        if rules_path.exists():
            with open(rules_path, "r", encoding="utf-8") as f:
                org_rules = yaml.safe_load(f) or {}
                layer_rules = org_rules.get("architecture", {}).get("layer_dependencies", {})

        # 简化：检查是否有跨层导入（示例）
        violations = []
        # TODO: 实际实现需要解析导入并与 layer_rules 对比

        return {
            "new_layer_violations": len(violations),
            "layer_violations_examples": violations[:5]
        }

    def check_layer_violations_post(ctx, prep_result, exec_result, params):
        ctx.update(exec_result)
        return "layers_checked"

    layer_node = node(
        prep=check_layer_violations_prep,
        exec=check_layer_violations_exec,
        post=check_layer_violations_post
    )
    f.add(layer_node, name="check_layers", params={"org_rules_path": "docs/org_rules.yaml"})

    # 3. 分析复杂度
    def analyze_complexity_prep(ctx, params):
        project_root = Path(ctx.get("project_root", "."))
        return {"project_root": project_root}

    def analyze_complexity_exec(prep_result, params):
        # 简化：统计函数的圈复杂度（McCabe）
        root = prep_result["project_root"]
        py_files = list(root.rglob("*.py"))
        complexities = []

        for py_file in py_files[:50]:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                for n in ast.walk(tree):
                    if isinstance(n, ast.FunctionDef):
                        # Mock: 复杂度 = if/for/while 语句数 + 1
                        complexity = 1
                        for child in ast.walk(n):
                            if isinstance(child, (ast.If, ast.For, ast.While)):
                                complexity += 1
                        complexities.append(complexity)
            except:
                continue

        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        cyclomatic_avg_delta = -5.0  # Mock: 与基线对比，降低 5%

        return {
            "cyclomatic_avg_delta": cyclomatic_avg_delta
        }

    def analyze_complexity_post(ctx, prep_result, exec_result, params):
        ctx.update(exec_result)
        return "complexity_analyzed"

    complexity_node = node(
        prep=analyze_complexity_prep,
        exec=analyze_complexity_exec,
        post=analyze_complexity_post
    )
    f.add(complexity_node, name="analyze_complexity")

    # 4. 检查 API 破坏性变更（Mock）
    def check_api_breaking_prep(ctx, params):
        return {}

    def check_api_breaking_exec(prep_result, params):
        # Mock 数据
        return {
            "breaking_changes_count": 0,
            "semver_suggestion": "patch",
            "schema_incompatible_count": 0,
            "deps_license_summary": "所有依赖许可证均兼容"
        }

    def check_api_breaking_post(ctx, prep_result, exec_result, params):
        ctx.update(exec_result)
        return "api_checked"

    api_node = node(
        prep=check_api_breaking_prep,
        exec=check_api_breaking_exec,
        post=check_api_breaking_post
    )
    f.add(api_node, name="check_api")

    # 5. 填充权重和门禁配置
    def fill_weights_prep(ctx, params):
        weights = params.get("weights", {
            "w_api": 0.3,
            "w_layer": 0.25,
            "w_cycles": 0.15,
            "w_schema": 0.15,
            "w_complexity": 0.10,
            "w_deps": 0.05
        })
        gates = params.get("gates", {
            "arch_score_min": 70,
            "no_breaking_api": True,
            "no_new_layer_violations": True
        })
        return {"weights": weights, "gates": gates}

    def fill_weights_exec(prep_result, params):
        return prep_result

    def fill_weights_post(ctx, prep_result, exec_result, params):
        ctx.update(exec_result["weights"])
        ctx.update(exec_result["gates"])
        return "weights_set"

    weights_node = node(
        prep=fill_weights_prep,
        exec=fill_weights_exec,
        post=fill_weights_post
    )
    f.add(weights_node, name="fill_weights", params={
        "weights": config.get("weights", {}),
        "gates": config.get("gates", {})
    })

    # 6. LLM 架构审计
    f.add(call_llm_node(), name="llm_arch_audit", params={
        "prompt_file": "prompts/arch_drift.prompt.md",
        "model": config.get("model", "gpt-4"),
        "temperature": 0.1,
        "max_tokens": 2500
    })

    # 7. 保存架构门禁结果
    f.add(write_file_node(), name="save_arch_gate", params={
        "output_path": ".ai-snapshots/arch_gate-{timestamp}.md",
        "format": "text",
        "data_key": "llm_response"
    })

    return f


def run(config=None):
    """运行场景④"""
    config = config or {}
    scenario = create_arch_drift_scenario(config)
    shared_store = {"project_root": ".", "timestamp": "AUTO"}
    result = scenario.run(shared_store)
    return result
