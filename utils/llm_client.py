import os
def call_llm(prompt, model='gpt-4', temperature=0.2, max_tokens=2000):
    # 示例：如果未配置 API Key，则返回 mock
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return f"[Mock LLM Response] {prompt[:100]}..."
    # TODO: 集成真实 LLM 调用
    return f"[Mock LLM Response] {prompt[:100]}..."
