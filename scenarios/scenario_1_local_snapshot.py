"""
场景①：本地快照与回滚（无远端依赖）

工作流：
1. GetFiles: 扫描项目文件
2. ParseCode: 解析代码结构
3. GenerateTopFiles: 生成关键文件列表（可选）
4. LLMSnapshot: AI 分析并生成快照
5. SaveSnapshot: 保存快照到本地
"""

from engine import flow, node
from nodes.common.get_files_node import get_files_node
from nodes.common.parse_code_node import parse_code_node
from nodes.common.call_llm_node import call_llm_node
from nodes.common.write_file_node import write_file_node
from nodes.common.snapshot_files_node import snapshot_files_node
from nodes.common.save_snapshot_node import save_snapshot_node


def create_local_snapshot_scenario(config):
    """创建本地快照场景"""
    f = flow()

    # 1. 获取文件
    f.add(get_files_node(), name="get_files", params={
        "patterns": config.get("file_patterns", ["**/*.py"]),
        "exclude": [".git/**", "__pycache__/**", ".ai-snapshots/**"]
    })

    # 2. 解析代码
    f.add(parse_code_node(), name="parse_code", params={"language": "python"})

    # 3. 生成关键文件列表（简化版）
    def gen_top_files_prep(ctx, params):
        files = ctx.get("files", [])
        return {"files": files}

    def gen_top_files_exec(prep_result, params):
        files = prep_result["files"]
        # 简化：取前 50 个文件
        top_files = files[:50]
        return {"top_files_list": "\n".join(f"- {f}" for f in top_files)}

    def gen_top_files_post(ctx, prep_result, exec_result, params):
        ctx.update(exec_result)
        return "top_files_generated"

    top_files_node = node(
        prep=gen_top_files_prep,
        exec=gen_top_files_exec,
        post=gen_top_files_post
    )
    f.add(top_files_node, name="gen_top_files")

    # 4. 创建文件快照（保存文件内容和哈希）
    f.add(snapshot_files_node(), name="snapshot_files")

    # 5. LLM 分析
    f.add(call_llm_node(), name="llm_snapshot", params={
        "prompt_file": "prompts/snapshot.prompt.md",
        "model": config.get("model", "gpt-4"),
        "temperature": 0.2,
        "max_tokens": 2000
    })

    # 6. 保存快照（JSON + MD）
    f.add(save_snapshot_node(), name="save_snapshot")

    return f

def run(config=None):
    config = config or {"file_patterns": ["**/*.py"]}
    scenario = create_local_snapshot_scenario(config)
    shared_store = {"project_root": ".", "timestamp": "AUTO"}
    result = scenario.run(shared_store)
    return result
