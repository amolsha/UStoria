import os
import json
from openai import OpenAI

# Anthropic (Claude)
import anthropic

# Google (Gemini)
import google.generativeai as genai

# ---- OpenAI setup ----
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- Anthropic setup ----
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ---- Gemini setup ----
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def complete(llm_name, prompt, temperature=0.7):
    """
    Dispatch completion request to the right LLM provider.
    Returns plain text response.
    """
    if llm_name in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]:
        return _complete_openai(llm_name, prompt, temperature)

    elif llm_name.startswith("claude"):
        return _complete_claude(llm_name, prompt, temperature)

    elif llm_name.startswith("gemini"):
        return _complete_gemini(llm_name, prompt, temperature)

    else:
        raise ValueError(f"Unsupported LLM: {llm_name}")


# ---------- Provider-specific implementations ----------

def _complete_openai(model, prompt, temperature=0.7):
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _complete_claude(model, prompt, temperature=0.7):
    """
    Anthropic Claude API
    Example model names: "claude-3-opus-20240229", "claude-3-sonnet-20240229"
    """
    response = anthropic_client.messages.create(
        model=model,
        max_tokens=800,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _complete_gemini(model, prompt, temperature=0.7):
    """
    Google Gemini API
    Example model names: "gemini-pro", "gemini-1.5-flash"
    """
    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(
        prompt,
        generation_config={"temperature": temperature}
    )
    return response.text.strip()
