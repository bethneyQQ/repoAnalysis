from engine import node
from pathlib import Path
import fnmatch

def get_files_node():
    """获取文件列表节点"""        
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
