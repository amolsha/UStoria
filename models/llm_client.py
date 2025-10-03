import os
from openai import OpenAI

# ---- OpenRouter setup ----
# Important: set OPEN_ROUTER_KEY in your environment
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_ROUTER_KEY"),
)


# model_mapper.py

def format_llm_name(model_name: str) -> str:
    """
    Map a raw model name to the OpenRouter namespaced format.

    Examples:
      "gpt-4o"              -> "openai/gpt-4o"
      "gpt-4-turbo"         -> "openai/gpt-4-turbo"
      "claude-3-opus"       -> "anthropic/claude-3-opus"
      "claude-3-haiku"      -> "anthropic/claude-3-haiku"
      "gemini-2.5-pro"      -> "google/gemini-2.5-pro"
      "deepseek-chat"       -> "deepseek/deepseek-chat"
      "grok-beta"           -> "xai/grok-beta"
    """

    model_name = model_name.lower().strip()

    if model_name.startswith("gpt-"):
        return f"openai/{model_name}"

    elif model_name.startswith("claude-"):
        return f"anthropic/{model_name}"

    elif model_name.startswith("gemini"):
        return f"google/{model_name}"

    elif model_name.startswith("deepseek"):
        return f"deepseek/{model_name}"

    elif model_name.startswith("grok"):
        return f"x-ai/{model_name}"

    elif model_name.startswith("llama"):
        return f"meta-llama/{model_name}"

    else:
        raise ValueError(f"Unknown model vendor for: {model_name}")


def complete(llm_name, prompt, temperature=0.7, max_tokens=1000):
    llm_name = format_llm_name(llm_name)
    response = client.chat.completions.create(
        model=llm_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
