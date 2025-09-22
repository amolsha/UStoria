import re
import pandas as pd

from models.storage import get_stories_for_project

CRITERIA = [
    "Well-formed", "Atomic", "Minimal",
    "Conceptually sound", "Problem-oriented", "Unambiguous",
    "Full sentence", "Estimable"
]

def _to_bool(val):
    if val is None:
        return False
    v = str(val).strip().lower()
    return v in ("1", "true", "yes", "y", "t", "on")

def parse_gold_labels_dataframe(df, project_id=None):
    """
    Return list of dicts: story_id, criterion, passed(bool), reason, repair.
    project_id helps to resolve story_text -> story_id if only text is provided.
    """
    rows = []

    # Normalize column names to lower and stripped
    cols = {c.lower().strip(): c for c in df.columns}

    # Long format detection: presence of 'criterion' column
    if "criterion" in cols:
        # require story_id or story_text
        if "story_id" in cols:
            sid_col = cols["story_id"]
            for _, r in df.iterrows():
                try:
                    story_id = int(r[sid_col])
                except Exception:
                    continue
                crit = str(r[cols["criterion"]]).strip()
                if not crit:
                    continue
                passed = _to_bool(r.get("passed") if "passed" in cols else r.get("pass"))
                reason = r.get("reason") if "reason" in cols else None
                repair = r.get("repair") if "repair" in cols else None
                rows.append({
                    "story_id": story_id,
                    "criterion": crit,
                    "passed": passed,
                    "reason": None if pd.isna(reason) else str(reason),
                    "repair": None if pd.isna(repair) else str(repair)
                })
        elif "story_text" in cols or "text" in cols:
            text_col = cols.get("story_text", cols.get("text"))
            # need project_id to resolve texts to story_id
            if not project_id:
                return []  # can't match
            # build mapping of story text->id (exact match)
            stories = get_stories_for_project(project_id)
            text_to_id = {s["text"].strip(): s["id"] for s in stories}
            for _, r in df.iterrows():
                text = str(r[text_col]).strip()
                story_id = text_to_id.get(text)
                if not story_id:
                    # try fuzzy/inexact match? skip for safety
                    continue
                crit = str(r[cols["criterion"]]).strip()
                passed = _to_bool(r.get("passed") if "passed" in cols else r.get("pass"))
                reason = r.get("reason") if "reason" in cols else None
                repair = r.get("repair") if "repair" in cols else None
                rows.append({
                    "story_id": story_id,
                    "criterion": crit,
                    "passed": passed,
                    "reason": None if pd.isna(reason) else str(reason),
                    "repair": None if pd.isna(repair) else str(repair)
                })
        return rows

    # Wide format detection: columns like "<Criterion>_pass" or "<Criterion>_reason"
    # Normalize headers and attempt to find for each criterion
    lower_cols = {c.lower(): c for c in df.columns}
    # Identify story id or text columns
    sid_col = lower_cols.get("story_id")
    text_col = lower_cols.get("story_text") or lower_cols.get("text")

    # Check if any criterion-specific pattern exists
    pattern_found = False
    for crit in CRITERIA:
        pass_col_name = f"{crit.lower().replace(' ', '_')}_pass"
        if pass_col_name in lower_cols:
            pattern_found = True
            break

    if pattern_found:
        # iterate rows, map story id or resolve text
        stories_map = {}
        if project_id and text_col:
            # prefetch stories for project to map text->id
            stories = get_stories_for_project(project_id)
            stories_map = {s["text"].strip(): s["id"] for s in stories}

        for _, r in df.iterrows():
            story_id = None
            if sid_col:
                story_id = r[lower_cols["story_id"]]
                try:
                    story_id = int(story_id)
                except Exception:
                    story_id = None
            elif text_col and project_id:
                txt = str(r[text_col]).strip()
                story_id = stories_map.get(txt)

            if not story_id:
                continue

            for crit in CRITERIA:
                pass_col = lower_cols.get(f"{crit.lower().replace(' ', '_')}_pass")
                reason_col = lower_cols.get(f"{crit.lower().replace(' ', '_')}_reason")
                repair_col = lower_cols.get(f"{crit.lower().replace(' ', '_')}_repair")
                if not pass_col:
                    continue
                passed = _to_bool(r.get(lower_cols[pass_col]) if isinstance(pass_col, str) and pass_col in lower_cols else r.get(pass_col))
                reason = None
                repair = None
                if reason_col:
                    reason = r.get(lower_cols[reason_col])
                if repair_col:
                    repair = r.get(lower_cols[repair_col])
                rows.append({
                    "story_id": int(story_id),
                    "criterion": crit,
                    "passed": passed,
                    "reason": None if pd.isna(reason) else str(reason),
                    "repair": None if pd.isna(repair) else str(repair)
                })
        return rows

    # If nothing recognized, return empty
    return []
