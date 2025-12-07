# app/services/llm_client.py

import os
from ..core.config import OPENAI_KEY
from ..core.logger import logger

OPENAI_ENABLED = bool(OPENAI_KEY)

def call_openai_completion(prompt: str, max_tokens: int = 300, temperature: float = 0.0):
    """
    Lightweight wrapper using GPT-3.5-turbo ChatCompletion.
    Returns text output from the LLM.
    """
    if not OPENAI_ENABLED:
        raise RuntimeError("OpenAI key not configured")

    try:
        import openai
        openai.api_key = OPENAI_KEY

        # Use ChatCompletion instead of Completion
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # updated from deprecated text-davinci-003
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Extract the generated text
        text = response['choices'][0]['message']['content'].strip()
        return text

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        raise RuntimeError(f"LLM request failed: {e}")


def is_enabled():
    """RAG engine uses this to check LLM availability."""
    return OPENAI_ENABLED
