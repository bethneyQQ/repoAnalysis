from engine import node
import json, os

def _safe_ts():
    return "20251017_224355"

def write_file_node():
    """写入文件节点"""
    def prep(ctx, params):
        output_path = params.get("output_path", "output.json")
        output_path = output_path.replace("{timestamp}", _safe_ts())
        data_key = params.get("data_key", "data")
        data = ctx.get(data_key, ctx)
        return {"output_path": output_path, "format": params.get("format", "json"), "data": data}

    def exec(prep_result, params):
        try:
            os.makedirs(os.path.dirname(prep_result["output_path"]) or ".", exist_ok=True)
            with open(prep_result["output_path"], "w", encoding="utf-8") as f:
                if prep_result["format"] == "json":
                    json.dump(prep_result["data"], f, indent=2, ensure_ascii=False, default=str)
                else:
                    f.write(str(prep_result["data"]))
            return {"success": True, "path": prep_result["output_path"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["output_file_path"] = exec_result["path"]
            return "file_written"
        ctx["write_error"] = exec_result["error"]
        return "write_failed"

    return node(prep=prep, exec=exec, post=post)
