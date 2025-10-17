from engine import node
from utils.llm_client import call_llm

def call_llm_node():
    """调用 LLM 节点"""
    def prep(ctx, params):
        template = params.get("prompt_template", "")
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
