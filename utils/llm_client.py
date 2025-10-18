"""
LLM 客户端：支持 OpenAI 和 Anthropic Claude API
"""

import os
import json


def call_llm(prompt, model='gpt-4', temperature=0.2, max_tokens=2000):
    """
    调用 LLM API

    支持的模型：
    - OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo
    - Anthropic: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-5-sonnet-20241022

    环境变量：
    - OPENAI_API_KEY: OpenAI API 密钥
    - ANTHROPIC_API_KEY: Anthropic API 密钥
    """

    # 检查是否使用 Claude
    if model.startswith('claude'):
        return _call_anthropic(prompt, model, temperature, max_tokens)
    else:
        return _call_openai(prompt, model, temperature, max_tokens)


def _call_anthropic(prompt, model, temperature, max_tokens):
    """调用 Anthropic Claude API"""
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        return f"[Mock LLM Response - Anthropic API key not found]\n\nPrompt preview:\n{prompt[:200]}..."

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        print(f"\n{'='*60}")
        print(f"🔵 Calling Anthropic API")
        print(f"Model: {model}")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Prompt preview: {prompt[:100]}...")
        print(f"{'='*60}\n")

        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        print(f"\n{'='*60}")
        print(f"✅ API Response received")
        print(f"Input tokens: {message.usage.input_tokens}")
        print(f"Output tokens: {message.usage.output_tokens}")
        print(f"Response length: {len(message.content[0].text)} chars")
        print(f"{'='*60}\n")

        return message.content[0].text

    except ImportError:
        return f"[Error] anthropic package not installed. Run: pip install anthropic\n\nPrompt preview:\n{prompt[:200]}..."
    except Exception as e:
        return f"[Error calling Anthropic API] {str(e)}\n\nPrompt preview:\n{prompt[:200]}..."


def _call_openai(prompt, model, temperature, max_tokens):
    """调用 OpenAI API"""
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        return f"[Mock LLM Response - OpenAI API key not found]\n\nPrompt preview:\n{prompt[:200]}..."

    try:
        import openai

        client = openai.OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    except ImportError:
        return f"[Error] openai package not installed. Run: pip install openai\n\nPrompt preview:\n{prompt[:200]}..."
    except Exception as e:
        return f"[Error calling OpenAI API] {str(e)}\n\nPrompt preview:\n{prompt[:200]}..."
