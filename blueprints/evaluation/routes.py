from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import storage, evaluator
from . import evaluation_bp

# evaluation_bp = Blueprint("evaluation", __name__, template_folder="../../templates")

@evaluation_bp.route("/", methods=["GET", "POST"])
def evaluate():
    if request.method == "POST":
        # Collect stories from textarea (one per line)
        stories_text = request.form.get("stories", "").strip()
        mode = request.form.get("mode", "minimal")  # minimal or rich

        if not stories_text:
            flash("Please enter at least one user story.", "warning")
            return redirect(url_for("evaluation.evaluate"))

        stories = [s.strip() for s in stories_text.split("\n") if s.strip()]
        all_results = []

        for story in stories:
            # 1. Save story
            story_id = storage.insert_story(story)

            # 2. Evaluate with LLM
            try:
                outcome = evaluator.evaluate_story(story, mode=mode)

                # 3. Persist each criterion result
                for criterion, details in outcome["criteria"].items():
                    storage.insert_evaluation(
                        story_id=story_id,
                        criterion=criterion,
                        passed=details["pass"],
                        reason=details["reason"],
                        repair=outcome["repairs"].get(criterion, "")
                    )

                # Attach DB id for traceability
                outcome["story_id"] = story_id
                all_results.append(outcome)

            except Exception as e:
                flash(f"Evaluation failed for story: {story} ({str(e)})", "danger")

        return render_template("evaluation.html", results=all_results, mode=mode)

    return render_template("evaluation.html")
