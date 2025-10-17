from engine import node
from utils.ast_parser import parse_file

def parse_code_node():
    """解析代码生成 AST 节点"""
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
