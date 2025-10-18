"""
快照文件节点 - 保存文件内容和哈希值用于回滚
"""

from engine import node
import json
import hashlib
from pathlib import Path
from datetime import datetime


def snapshot_files_node():
    """创建文件快照节点（保存文件内容和哈希）"""

    def prep(ctx, params):
        files = ctx.get("files", [])
        project_root = ctx.get("project_root", ".")
        return {
            "files": files,
            "project_root": project_root
        }

    def exec(prep_result, params):
        files = prep_result["files"]
        project_root = prep_result["project_root"]

        snapshot_data = {
            "timestamp": datetime.now().isoformat(),
            "project_root": project_root,
            "files": {}
        }

        for file_path in files:
            try:
                full_path = Path(project_root) / file_path
                if full_path.exists() and full_path.is_file():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 计算文件哈希
                    file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

                    snapshot_data["files"][str(file_path)] = {
                        "content": content,
                        "hash": file_hash,
                        "size": len(content)
                    }
            except Exception as e:
                print(f"Warning: Failed to snapshot {file_path}: {e}")

        return {
            "snapshot_data": snapshot_data,
            "file_count": len(snapshot_data["files"])
        }

    def post(ctx, prep_result, exec_result, params):
        ctx["snapshot_data"] = exec_result["snapshot_data"]
        ctx["snapshot_file_count"] = exec_result["file_count"]
        return "snapshot_created"

    return node(prep=prep, exec=exec, post=post)
