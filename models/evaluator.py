import json
from models import llm_client, prompts

def evaluate_story(story: str, mode: str = "minimal") -> dict:
    criteria_list = [
        "Well-formed", "Atomic", "Complete", "Consistent",
        "Unambiguous", "Testable", "Traceable", "Feasible"
    ]

    if mode == "minimal":
        prompt = prompts.INDIVIDUAL_PROMPT_MINIMAL.format(
            criteria_list=", ".join(criteria_list),
            story=story
        )
    else:
        prompt = prompts.INDIVIDUAL_PROMPT_RICH.format(
            criteria_list=", ".join(criteria_list),
            story=story
        )

    response = llm_client.complete(prompt)

    try:
        data = json.loads(response)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from LLM: {response[:200]}...")
