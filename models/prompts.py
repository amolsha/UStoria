# models/prompts.py

# Minimal prompt: only descriptions of criteria
INDIVIDUAL_PROMPT_MINIMAL = """
Evaluate the following user story against these individual-level QUS criteria:
{criteria_list}

User story:
"{story}"

INSTRUCTIONS:
- If multiple criteria are provided, evaluate the story against all of them.
- If ONLY ONE criterion is provided, then evaluate ONLY that criterion. 
  Do not mention or add other criteria in the output.
- For each criterion, return PASS/FAIL and a one-sentence justification (why it fails or why it passes).
- If the story fails a criterion, propose a concise repair (a single improved user story) that addresses that criterion.

Return ONLY a JSON object with the following structure:
{{
  "story": "<original story>",
  "criteria": {{
     "<CriterionName>": {{ "pass": true|false, "reason": "<short explanation>" }},
     ...
  }},
  "repairs": {{
     "<CriterionName>": "<suggested improved user story text>",
     ...
  }}
}}
Do not add any extra commentary.Use short sentences in reasons and repairs.
"""

# Rich prompt: with examples
INDIVIDUAL_PROMPT_RICH = """
You are an expert requirements engineer. Use the Quality User Story (QUS) framework to evaluate the user story below.
Criteria: {criteria_list}

Guidelines:
- Well-formed: includes role + feature/function. Example bad: "I want to reset password" (no role).
- Atomic: only one feature. Example bad: "As a user, I want to log in and view my profile".
- Minimal: no implementation details. Example bad: "First, implement X, then add Y".
- Conceptually sound: feature + rationale. Example bad: "As a user, I would like to improve my data".
- Problem-oriented: describe problem, not solution. Example bad: "I want a button to reset password".
- Unambiguous: avoid vague terms. Example bad: "As a user, I want a secure login".
- Full sentence: grammatically correct. Example bad: "As user, password reset".
- Estimable: specific enough for estimation. Example bad: "As a user, I want to update my profile".

User story:
"{story}"

INSTRUCTIONS:
- If multiple criteria are provided, evaluate the story against all of them.
- If ONLY ONE criterion is provided, then evaluate ONLY that criterion. 
  Do not mention or add other criteria in the output.
- For each criterion, return PASS/FAIL and a one-sentence justification (why it fails or why it passes).
- If the story fails a criterion, propose a concise repair (a single improved user story) that addresses that criterion.

Return ONLY valid JSON following this shape:
{{
  "story": "<original story>",
  "criteria": {{
     "<CriterionName>": {{ "pass": true|false, "reason": "<short explanation>" }},
     ...
  }},
  "repairs": {{
     "<CriterionName>": "<suggested improved user story text>",
     ...
  }}
}}
No extra text. Use short sentences in reasons and repairs.
"""


def get_prompt(prompt_type: str) -> str:
    if prompt_type.lower() == "minimal":
        return INDIVIDUAL_PROMPT_MINIMAL
    elif prompt_type.lower() == "rich":
        return INDIVIDUAL_PROMPT_RICH
    else:
        raise ValueError(f"Unknown prompt type: {prompt_type}")