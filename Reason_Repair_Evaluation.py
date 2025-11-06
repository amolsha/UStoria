import pandas as pd
import json
from openai import OpenAI
from tqdm import tqdm

# ---------- CONFIGURATION ----------
DATA_FILE = "evaluations.csv"      # input from your SQLite export
META_RATER_MODEL = "gpt-4o-mini"    # or "gpt-4.1-mini"
TEMPERATURE = 0
SAVE_FILE = "meta_eval_results.csv"

# ---------- QUALITY CRITERIA (QUS FRAMEWORK) ----------
# Based on your specified eight criteria

QUS_DEFS = {
    # --- Syntactic ---
    "Well-formed": "A user story includes at least a role and a means.",
    "Atomic": "A user story expresses a requirement for exactly one feature.",
    "Minimal": "A user story contains nothing more than role, means, and ends.",

    # --- Semantic ---
    "Conceptually sound": "The means expresses a feature and the ends expresses a rationale.",
    "Problem-oriented": "A user story only specifies the problem, not the solution to it.",
    "Unambiguous": "A user story avoids terms or abstractions that lead to multiple interpretations.",

    # --- Pragmatic ---
    "Full sentence": "A user story is a well-formed full sentence.",
    "Estimatable": "A story does not denote a coarse-grained requirement that is difficult to plan and prioritize."
}

client = OpenAI()

# ---------- PROMPTS ----------

def get_repair_prompt(criterion, repaired_story):
    """Prompt for Repair Success evaluation."""
    return f"""
You are an expert in requirements engineering and agile user story quality.
Determine whether the following *repaired* user story conforms to the specified QUS criterion.

Criterion: {criterion} — {QUS_DEFS.get(criterion, "")}

Repaired User Story:
\"\"\"{repaired_story}\"\"\"

Respond strictly as JSON: {{"conforms":"Yes"}} or {{"conforms":"No"}}.
"""

def get_reason_prompt(criterion, original_story, reason_text):
    """Prompt for Reason Adequacy evaluation (requires original story)."""
    if not original_story or str(original_story).strip() == "":
        return None
    return f"""
You are an expert in requirements engineering and user story quality.
Evaluate how accurate the model's *reason* is for marking a user story as non-conforming.

Criterion: {criterion} — {QUS_DEFS.get(criterion, "")}

Original User Story:
\"\"\"{original_story}\"\"\"

Model's reason:
\"\"\"{reason_text}\"\"\"

Rate correctness of the reason on a 3-point scale:
1 = incorrect or irrelevant
2 = partially correct
3 = fully correct

Respond strictly as JSON: {{"rating": 1}} or 2 or 3.
"""

# ---------- META-RATER CALL ----------
def call_meta_rater(prompt):
    """Send prompt to meta-rater LLM and parse JSON response."""
    try:
        response = client.chat.completions.create(
            model=META_RATER_MODEL,
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": "You are a precise evaluator who outputs only valid JSON responses."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except Exception as e:
        print("⚠️ Error:", e)
        return None

# ---------- MAIN EVALUATION ----------
def evaluate_rsr_ras():
    df = pd.read_csv(DATA_FILE)
    results = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Evaluating RSR & RAS"):
        story_id = row["story_id"]
        model = row["model"]
        context = row["context"]
        criterion = row["criterion"]
        orig_label = str(row["original_label"]).strip()
        reason = str(row.get("reason", "")).strip()
        repair = str(row.get("repair", "")).strip()
        story = str(row.get("original_story", "")).strip()

        # Evaluate only failed stories that have a repair
        if orig_label.lower() == "no" and repair:
            # --- Repair Success ---
            repair_prompt = get_repair_prompt(criterion, repair)
            r_response = call_meta_rater(repair_prompt)
            conforms = None
            if r_response and "conforms" in r_response:
                conforms = r_response["conforms"].strip()

            # --- Reason Adequacy ---
            ras_score = None
            if reason and story:
                reason_prompt = get_reason_prompt(criterion, story, reason)
                if reason_prompt:
                    q_response = call_meta_rater(reason_prompt)
                    if q_response and "rating" in q_response:
                        ras_score = q_response["rating"]
            else:
                # Missing story text or reason — skip RAS
                ras_score = None

            results.append({
                "story_id": story_id,
                "model": model,
                "context": context,
                "criterion": criterion,
                "repair_conforms": conforms,
                "reason_rating": ras_score
            })

    out = pd.DataFrame(results)
    out.to_csv(SAVE_FILE, index=False)
    print(f"✅ Saved detailed meta-rater results to '{SAVE_FILE}'")

    # ---------- COMPUTE METRICS ----------
    summary = []

    for (m, c), group in out.groupby(["model", "context"]):
        n_failed = len(group)
        n_repaired_conforming = (group["repair_conforms"] == "Yes").sum()
        rsr = n_repaired_conforming / n_failed if n_failed else 0

        valid_ratings = group["reason_rating"].dropna()
        ras = valid_ratings.mean() / 3 if not valid_ratings.empty else 0

        summary.append({
            "model": m,
            "context": c,
            "RSR": round(rsr, 3),
            "RAS": round(ras, 3),
            "N_failed": n_failed
        })

    summary_df = pd.DataFrame(summary)
    print("\n===== SUMMARY (per-model × context) =====")
    print(summary_df.to_string(index=False))

    summary_df.to_csv("meta_eval_summary.csv", index=False)
    print("✅ Saved summary to 'meta_eval_summary.csv'")

# ---------- RUN ----------
if __name__ == "__main__":
    evaluate_rsr_ras()
