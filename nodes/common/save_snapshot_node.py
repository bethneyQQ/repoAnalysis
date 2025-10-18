"""
保存快照节点 - 将快照数据保存为 JSON 文件
"""

from engine import node
import json
from pathlib import Path
from datetime import datetime


def save_snapshot_node():
    """保存快照到 JSON 文件"""

    def prep(ctx, params):
        snapshot_data = ctx.get("snapshot_data", {})
        llm_response = ctx.get("llm_response", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return {
            "snapshot_data": snapshot_data,
            "llm_response": llm_response,
            "timestamp": timestamp
        }

    def exec(prep_result, params):
        snapshot_data = prep_result["snapshot_data"]
        llm_response = prep_result["llm_response"]
        timestamp = prep_result["timestamp"]

        # 添加 LLM 分析到快照数据
        snapshot_data["llm_analysis"] = llm_response

        # 保存到 .ai-snapshots 目录
        snapshots_dir = Path(".ai-snapshots")
        snapshots_dir.mkdir(exist_ok=True)

        snapshot_file = snapshots_dir / f"snapshot-{timestamp}.json"

        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2, ensure_ascii=False)

        # 同时保存 Markdown 报告
        md_file = snapshots_dir / f"snapshot-{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(llm_response)

        return {
            "snapshot_file": str(snapshot_file),
            "md_file": str(md_file),
            "timestamp": timestamp
        }

    def post(ctx, prep_result, exec_result, params):
        ctx["snapshot_file"] = exec_result["snapshot_file"]
        ctx["snapshot_id"] = exec_result["timestamp"]
        print(f"✅ Snapshot saved: {exec_result['snapshot_file']}")
        print(f"✅ Report saved: {exec_result['md_file']}")
        return "snapshot_saved"

    return node(prep=prep, exec=exec, post=post)
