import json
import time
from models import llm_client, prompts
from models.prompts import INDIVIDUAL_PROMPT_MINIMAL, INDIVIDUAL_PROMPT_RICH

# Define evaluation criteria once (extendable)
CRITERIA = [
"Well-formed",
"Atomic",
"Minimal",
"Conceptually sound",
"Problem-oriented",
"Unambiguous",
"Full sentence",
"Estimable"
]

PROMPTS = {
    "minimal": INDIVIDUAL_PROMPT_MINIMAL,
    "rich": INDIVIDUAL_PROMPT_RICH,
}

import json
import re

def parse_llm_json(response_text: str):
    """
    Safely extract JSON object from LLM response text.

    Parameters:
        response_text (str): The raw LLM output (may have extra text).

    Returns:
        dict: Parsed JSON object.
    """
    # Regex to capture first {...} JSON block
    match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM response.")

    json_str = match.group(0)

    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        # Optionally: try to fix common issues like trailing commas
        json_str_fixed = re.sub(r",\s*}", "}", json_str)
        json_str_fixed = re.sub(r",\s*]", "]", json_str_fixed)
        try:
            data = json.loads(json_str_fixed)
            return data
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse JSON from LLM response: {e}\nResponse was:\n{response_text}")


def evaluate_story(story_text, llm_name, prompt, temperature=0.7):
    """
    Evaluate a user story using an LLM against a set of criteria.
    Returns dict: {criterion: {"passed": bool, "reason": str, "repair": str}}
    """
    prompt_template = PROMPTS.get(prompt, INDIVIDUAL_PROMPT_MINIMAL)
    eval_prompt = prompt_template.format(
        story=story_text,
        criteria_list="\n".join(CRITERIA),
    )

    # Query the LLM
    response = llm_client.complete(
        llm_name=llm_name,
        prompt=eval_prompt,
        temperature=temperature,
    )
    print("Reslponse::::::")
    print(response)
    # Parse response
    results=""
    try:
        # Expect structured JSON
        results = parse_llm_json(response)
    except Exception as e:
        print(e)
        # Fallback: if LLM output is free text, attempt heuristic extraction
        # results = fallback_parse(response)

    # Assume CRITERIA is a list of criterion names
    normalized = {}
    criteria_results = results.get("criteria", {})
    repairs = results.get("repairs", {})

    for criterion in CRITERIA:
        entry = criteria_results.get(criterion, {})
        normalized[criterion] = {
            "passed": entry.get("pass", False),
            "reason": entry.get("reason", ""),
            "repair": repairs.get(criterion, "")
        }

    return normalized


def fallback_parse(text):
    """
    Simple heuristic parser if JSON parsing fails.
    (Looks for keywords like PASS/FAIL and repair suggestions.)
    """
    parsed = {}
    for criterion in CRITERIA:
        lower_text = text.lower()
        if criterion.lower() in lower_text:
            passed = "pass" in lower_text or "yes" in lower_text
            parsed[criterion] = {
                "passed": passed,
                "reason": f"Heuristic parse for {criterion}",
                "repair": "N/A",
            }
        else:
            parsed[criterion] = {"passed": False, "reason": "Not found", "repair": ""}
    return parsed

