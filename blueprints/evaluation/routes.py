import asyncio

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import time

from blueprints.evaluation import evaluation_bp
from models import storage, evaluator, llm_client, prompts
from models.performance_analysis import compute_metrics
from models.storage import get_runs


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

CRITERIA = [
    "Well-formed", "Atomic", "Minimal",
    "Conceptually sound", "Problem-oriented", "Unambiguous",
    "Full sentence", "Estimable"
]

# @evaluation_bp.route("/evaluate_by_criterion", methods=["GET", "POST"])
# def evaluate_by_criterion():
#     projects = storage.get_all_projects()
#     selected_project = request.args.get("project_id", type=int)
#     selected_batch = request.args.get("batch_id", type=int)
#
#     batches = storage.get_batches_of_project(selected_project) if selected_project else []
#
#     if request.method == "POST":
#         project_id = int(request.form["project_id"])
#         batch_id = int(request.form["batch_id"])
#         criterion = request.form["criterion"]
#         llm_name = request.form["llm"]
#         temperature = float(request.form.get("temperature", 0.7))
#         prompt_type = request.form["prompt_type"]   # still needed
#
#         start_time = time.time()
#         run_id = storage.insert_run(
#             project_id, batch_id, llm_name,
#             prompt_type, temperature,
#             mode="criterion"
#         )
#
#         stories = storage.get_stories_in_batch(batch_id)
#
#         for story in stories:
#             results = evaluator.evaluate_story_by_criterion(
#                 story["text"],
#                 llm_name=llm_name,
#                 criterion=criterion,
#                 prompt=prompts.get_prompt(prompt_type),
#                 temperature=temperature
#             )
#
#             for criterion, outcome in results.items():
#                 storage.insert_evaluation(
#                     run_id=run_id,
#                     story_id=story["id"],
#                     criterion=criterion,
#                     passed=outcome.get("passed", False),
#                     reason=outcome.get("reason", ""),
#                     repair=outcome.get("repair", "")
#                 )
#
#
#         # Finish run
#         duration = round(time.time() - start_time, 2)
#         storage.finish_run(run_id, duration)
#
#         flash(f"Evaluation complete for criterion: {criterion} in {duration} seconds!", "success")
#         return redirect(url_for("evaluation.view_run", run_id=run_id))
#
#     return render_template(
#         "evaluate_by_criterion.html",
#         projects=projects,
#         batches=batches,
#         selected_project=selected_project,
#         selected_batch=selected_batch,
#         criteria=CRITERIA
#     )

@evaluation_bp.route("/evaluate_by_criterion", methods=["GET", "POST"])
def evaluate_by_criterion():
    projects = storage.get_all_projects()
    selected_project = request.args.get("project_id", type=int)
    selected_batch = request.args.get("batch_id", type=int)

    batches = storage.get_batches_of_project(selected_project) if selected_project else []

    if request.method == "POST":
        project_id = int(request.form["project_id"])
        batch_id = int(request.form["batch_id"])
        criterion = request.form["criterion"]
        llm_name = request.form["llm"]
        temperature = float(request.form.get("temperature", 0.7))
        prompt_type = request.form["prompt_type"]

        start_time = time.time()

        # Register this evaluation run in DB
        run_id = storage.insert_run(
            project_id, batch_id, llm_name,
            prompt_type, temperature,
            mode="criterion"
        )

        # Fetch stories from DB
        stories = storage.get_stories_in_batch(batch_id)   # ≈ 60 stories

        # --- ASYNC BATCH EVALUATION ---
        from models.evaluator_async import evaluate_stories_async
        from models import prompts

        async def run_async_eval():
            return await evaluate_stories_async(
                stories=stories,
                llm_name=llm_name,
                prompt_template=prompts.get_prompt(prompt_type),
                criterion=criterion,
                batch_size=10,      # divide into 10-sized batches
                concurrency=5,      # run 5 batches at once
            )

        # Run async evaluation (Flask is sync, so wrap it)
        results = asyncio.run(run_async_eval())

        # --- STORE RESULTS ---
        for story_id, criteria_dict in results.items():
            outcome = criteria_dict.get(criterion, {})
            storage.insert_evaluation(
                run_id=run_id,
                story_id=story_id,
                criterion=criterion,
                passed=outcome.get("passed", False),
                reason=outcome.get("reason", ""),
                repair=outcome.get("repair", "")
            )

        # Finish run
        duration = round(time.time() - start_time, 2)
        storage.finish_run(run_id, duration)

        flash(f"Evaluation complete for criterion: {criterion} in {duration} seconds!", "success")
        return redirect(url_for("evaluation.view_run", run_id=run_id))

    return render_template(
        "evaluate_by_criterion.html",
        projects=projects,
        batches=batches,
        selected_project=selected_project,
        selected_batch=selected_batch,
        criteria=CRITERIA
    )


@evaluation_bp.route("/performance", methods=["GET", "POST"])
def performance():
    # ✅ Use the helper instead of manual query
    runs = get_runs()  # returns list of (id, name)

    # Convert to a simple iterable structure for HTML rendering
    runs = [{"id": r[0], "name": r[1]} for r in runs]

    selected_runs = request.form.getlist("run_ids")
    all_metrics = {}

    if selected_runs:
        for run_id in selected_runs:
            metrics = compute_metrics(run_id)
            if metrics:
                all_metrics[run_id] = metrics

    return render_template("performance.html", runs=runs, all_metrics=all_metrics)

