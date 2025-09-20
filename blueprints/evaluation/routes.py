from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import time

from blueprints.evaluation import evaluation_bp
from models import storage, evaluator, llm_client, prompts

@evaluation_bp.route("/evaluate", methods=["GET", "POST"])
def evaluate():
    projects = storage.get_all_projects()
    selected_project = request.args.get("project_id", type=int)
    selected_batch = request.args.get("batch_id", type=int)

    batches = storage.get_batches_of_project(selected_project) if selected_project else []

    if request.method == "POST":
        project_id = int(request.form["project_id"])
        batch_id = int(request.form["batch_id"])
        llm_name = request.form["llm"]
        prompt_type = request.form["prompt_type"]
        temperature = float(request.form.get("temperature") or 0.7)

        # Create a run entry
        run_id = storage.insert_run(project_id, batch_id, llm_name, prompt_type, temperature)

        # Start timer
        start_time = time.time()

        # Get stories in batch
        stories = storage.get_stories_in_batch(batch_id)

        # Evaluate each story
        for story in stories:
            results = evaluator.evaluate_story(
                story["text"],
                llm_name=llm_name,
                prompt=prompts.get_prompt(prompt_type),
                temperature=temperature
            )
            for criterion, outcome in results.items():
                storage.insert_evaluation(
                    run_id=run_id,
                    story_id=story["id"],
                    criterion=criterion,
                    passed=outcome.get("passed", False),
                    reason=outcome.get("reason", ""),
                    repair=outcome.get("repair", "")
                )

        # Finish run
        duration = round(time.time() - start_time, 2)
        storage.finish_run(run_id, duration)

        flash(f"Evaluation complete in {duration} seconds!", "success")
        return redirect(url_for("evaluation.view_run", run_id=run_id))

    return render_template(
        "evaluate.html",
        projects=projects,
        batches=batches,
        selected_project=selected_project,
        selected_batch=selected_batch
    )


@evaluation_bp.route("/runs/<int:run_id>")
def view_run(run_id):
    run = storage.get_runs_for_batch(0)  # placeholder: fetch run info
    evaluations = storage.get_evaluations_for_run(run_id)
    return render_template("view_run.html", run_id=run_id, evaluations=evaluations)

@evaluation_bp.route("/run_summary/<int:run_id>")
def run_summary(run_id):
    summary = storage.get_run_summary(run_id)

    # Extract chart data
    criteria = [row["criterion"] for row in summary]
    passed = [row["passed_count"] for row in summary]
    failed = [row["failed_count"] for row in summary]
    totals = [row["total"] for row in summary]

    return render_template(
        "run_summary.html",
        run_id=run_id,
        criteria=criteria,
        passed=passed,
        failed=failed,
        totals=totals,
    )
