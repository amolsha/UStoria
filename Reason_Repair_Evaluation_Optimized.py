import pandas as pd
import json
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- CONFIGURATION ----------
DATA_FILE = "evaluations_sampled.csv"
META_RATER_MODEL = "gpt-5-nano-2025-08-07"
TEMPERATURE = 0
SAVE_FILE = "meta_eval_results.csv"
MAX_WORKERS = 8   # tune based on rate limits

client = OpenAI()

# ---------- QUALITY CRITERIA (QUS FRAMEWORK) ----------
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
    "Estimable": "A story does not denote a coarse-grained requirement that is difficult to plan and prioritize."
}
#You are a strict expert evaluator of agile user story quality.

# ---------- COMBINED PROMPT ----------
def get_combined_prompt(criterion, original_story, reason, repaired_story,role):
    return f"""
{role}

Criterion: {criterion} — {QUS_DEFS.get(criterion, "")}

Original User Story:
\"\"\"{original_story}\"\"\"

Model's reason for non-conformance:
\"\"\"{reason}\"\"\"

Repaired User Story:
\"\"\"{repaired_story}\"\"\"

Tasks:
1. Decide whether the repaired user story conforms to the criterion.
2. Rate the correctness of the model's reason:
   1 = incorrect or irrelevant
   2 = partially correct
   3 = fully correct

Respond strictly as JSON:
{{
  "repair_conforms": "Yes" or "No",
  "reason_rating": 1 or 2 or 3
}}
"""

# ---------- META-RATER CALL ----------
def call_meta_rater(prompt):
    response = client.chat.completions.create(
        model=META_RATER_MODEL,
        #temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": "Return only valid JSON. No explanation."},
            {"role": "user", "content": prompt}
        ]
    )
    content = response.choices[0].message.content.strip()
    return json.loads(content)

# ---------- SINGLE ROW PROCESSOR ----------
def process_row(row):
    orig_label = str(row["original_label"]).strip().lower()
    repair = str(row.get("repair", "")).strip()

    # Evaluate only failed stories with a repair
    if orig_label != "no" or not repair:
        return None

    role=f"""    
    You are a formal quality auditor evaluating requirement artifacts.
    You apply criteria literally and conservatively, without interpretation beyond the definition.
    """

    # Strict Academic Reviewer (baseline)
    # You are a strict academic reviewer specializing in requirements engineering.
    # You evaluate user stories only against the stated criterion.
    # You do not infer missing intent or give the benefit of the doubt.

    # Industry Requirements Engineer
    # You are a senior industry requirements engineer with extensive agile experience.
    # You judge user stories as they would be used in practice, but still adhere strictly to the stated criterion.

    # Formal Quality Auditor (ISO / standard-oriented)
    # You are a formal quality auditor evaluating requirement artifacts.
    # You apply criteria literally and conservatively, without interpretation beyond the definition.

    prompt = get_combined_prompt(
        criterion=row["criterion"],
        original_story=str(row.get("original_story", "")).strip(),
        reason=str(row.get("reason", "")).strip(),
        repaired_story=repair,
        role=role
    )

    #print(prompt)

    try:
        result = call_meta_rater(prompt)
        return {
            "story_id": row["story_id"],
            "model": row["model"],
            "context": row["context"],
            "criterion": row["criterion"],
            "repair_conforms": result.get("repair_conforms"),
            "reason_rating": result.get("reason_rating")
        }
    except Exception as e:
        print("⚠️ Meta-rater error:", e)
        return None

# ---------- MAIN EVALUATION ----------
def evaluate_rsr_ras():
    df = pd.read_csv(DATA_FILE)
    results = []

    rows = [row for _, row in df.iterrows()
            if str(row["original_label"]).strip().lower() == "no"
            and str(row.get("repair", "")).strip()]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_row, row) for row in rows]

        for future in tqdm(as_completed(futures),
                           total=len(futures),
                           desc="Evaluating RSR & RAS"):
            res = future.result()
            if res:
                results.append(res)

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
