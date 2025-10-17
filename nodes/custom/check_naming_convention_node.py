from engine import node
from utils.naming_checker import check_naming_convention

def check_naming_convention_node():
    """检查命名规范节点"""
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
