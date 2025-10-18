from engine import node
from utils.llm_client import call_llm
from pathlib import Path

def call_llm_node():
    """调用 LLM 节点

    支持两种方式提供 Prompt：
    1. prompt_template: 直接提供模板字符串
    2. prompt_file: 提供模板文件路径（相对于项目根目录）
    """
    def prep(ctx, params):
        # 优先从文件加载模板
        template = params.get("prompt_template", "")
        prompt_file = params.get("prompt_file", "")

        if prompt_file:
            # 从文件加载模板
            file_path = Path(prompt_file)
            if not file_path.is_absolute():
                # 相对路径，相对于项目根目录
                project_root = Path(ctx.get("project_root", "."))
                file_path = project_root / prompt_file

            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    template = f.read()
            else:
                raise FileNotFoundError(f"Prompt file not found: {file_path}")

        # 防止 KeyError：允许模板里出现缺失字段
        class D(dict):
            def __missing__(self, k): return ""
        prompt = template.format_map(D(**ctx))
        return {
            "prompt": prompt,
            "model": params.get("model", "gpt-4"),
            "temperature": params.get("temperature", 0.2),
            "max_tokens": params.get("max_tokens", 2000)
        }

    def exec(prep_result, params):
        try:
            resp = call_llm(
                prompt=prep_result["prompt"],
                model=prep_result["model"],
                temperature=prep_result["temperature"],
                max_tokens=prep_result["max_tokens"]
            )
            return {"success": True, "response": resp}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def post(ctx, prep_result, exec_result, params):
        if exec_result["success"]:
            ctx["llm_response"] = exec_result["response"]
            return "llm_complete"
        ctx["llm_error"] = exec_result["error"]
        return "llm_failed"

    return node(prep=prep, exec=exec, post=post)
