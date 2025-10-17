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
