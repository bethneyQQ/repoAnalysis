"""
Token counting utilities for managing LLM context limits.
Uses tiktoken for accurate token estimation.
"""
import tiktoken

# Default model for token counting - using cl100k_base which is used by most modern models
DEFAULT_ENCODING = "cl100k_base"

def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """
    Count the number of tokens in a text string.

    Args:
        text: The text to count tokens for
        encoding_name: The encoding to use (default: cl100k_base)

    Returns:
        Number of tokens in the text
    """
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback to rough estimation if tiktoken fails
        # Approximate: 1 token ≈ 4 characters
        return len(text) // 4


def estimate_tokens(text: str) -> int:
    """
    Quick estimation of tokens without using tiktoken.
    Uses the approximation that 1 token ≈ 4 characters.

    Args:
        text: The text to estimate tokens for

    Returns:
        Estimated number of tokens
    """
    return len(text) // 4
