import asyncio
import json
import re
import time
from typing import List
from models import llm_client, prompts

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

# -------------------------------
# Utility: safe JSON parsing
# -------------------------------
def parse_llm_json(response_text: str):
    """
    Extract and parse the first valid JSON object or array from an LLM response.

    Handles cases like:
    ```json
    { ... }
    ```
    or
    ```json
    [ { ... }, { ... } ]
    ```
    """

    # 1️⃣ Remove Markdown code fences like ```json ... ```
    cleaned = re.sub(r"```(?:json)?", "", response_text, flags=re.IGNORECASE).strip()

    # 2️⃣ Find first JSON array or object
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object or array found in LLM response.")

    json_str = match.group(0).strip()

    # 3️⃣ Try parsing robustly
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Common cleanup fixes for trailing commas
        json_str_fixed = re.sub(r",\s*([}\]])", r"\1", json_str)
        try:
            return json.loads(json_str_fixed)
        except json.JSONDecodeError as e2:
            raise ValueError(
                f"Failed to parse JSON after cleanup: {e2}\n"
                f"Original response snippet:\n{response_text[:500]}"
            )


# -------------------------------
# Async evaluator
# -------------------------------
async def evaluate_stories_batch(
    stories: List[dict],
    llm_name: str,
    prompt_template: str,
    criterion: str = None,
    temperature: float = 0.7,
):
    """
    Evaluate a list of stories (in one API call).
    stories: list of dicts with {id, text}
    Returns: dict {story_id: {criterion: {passed, reason, repair}}}
    """
    # Format stories for prompt
    stories_text = "\n\n".join(
        [f"Story {s['id']}: {s['text']}" for s in stories]
    )

    # Build prompt
    if criterion:
        criteria_list = criterion  # single criterion mode
    else:
        criteria_list = "\n".join(CRITERIA)

    eval_prompt = prompt_template.format(
        stories_list=stories_text,
        criteria_list=criteria_list,
    )

    # Call LLM (async wrapper from llm_client)
    response = await llm_client.async_complete(
        llm_name=llm_name,
        prompt=eval_prompt,
        temperature=temperature,
    )

    results = parse_llm_json(response)
    print(":: RESULT ::")
    # print(results)

    normalized = {}
    for s in stories:
        sid = s["id"]
        normalized[sid] = {}

        # Normalize results to always be a list
        if isinstance(results, dict):
            # maybe the LLM returned a single story object instead of a list
            results = [results]

        elif not isinstance(results, list):
            # unexpected type
            raise ValueError(f"Unexpected results type: {type(results)}")

        # Convert list of results into a dict keyed by story_id
        # results_by_sid = {str(r["story_id"]): r for r in results if "story_id" in r}

        results_by_sid = {
            re.search(r"\d+", str(r["story_id"])).group(0) if re.search(r"\d+", str(r["story_id"])) else str(
                r["story_id"]): r
            for r in results
            if "story_id" in r
        }

        # Fetch criteria and repairs for a specific story_id
        criteria_results = results_by_sid.get(str(sid), {}).get("criteria", {})
        repairs = results_by_sid.get(str(sid), {}).get("repairs", {})

        for crit in ( [criterion] if criterion else CRITERIA ):
            entry = criteria_results.get(crit, {})
            normalized[sid][crit] = {
                "passed": entry.get("pass", False),
                "reason": entry.get("reason", ""),
                "repair": repairs.get(crit, ""),
            }
    print(normalized)
    return normalized


async def evaluate_stories_async(
    stories: List[dict],
    llm_name: str,
    prompt_template: str,
    criterion: str = None,
    batch_size: int = 10,
    concurrency: int = 5,
):
    """
    Run story evaluation concurrently in batches.
    """
    sem = asyncio.Semaphore(concurrency)

    async def run_batch(batch):
        async with sem:
            return await evaluate_stories_batch(
                batch, llm_name, prompt_template, criterion
            )

    # Slice stories into chunks
    tasks = []
    for i in range(0, len(stories), batch_size):
        chunk = stories[i : i + batch_size]
        tasks.append(run_batch(chunk))

    results = await asyncio.gather(*tasks)

    # Merge all batch results
    merged = {}
    for r in results:
        merged.update(r)

    return merged
