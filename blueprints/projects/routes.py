from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import storage, evaluator

from . import projects_bp

@projects_bp.route("/projects", methods=["GET", "POST"])
def list_projects():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        if not name:
            flash("Project name is required", "error")
        else:
            storage.insert_project(name, description)
            flash("Project created successfully", "success")
            return redirect(url_for("projects.list_projects"))
    projects = storage.get_all_projects()
    return render_template("projects.html", projects=projects)


@projects_bp.route("/projects/delete/<int:project_id>", methods=["POST"])
def delete_project(project_id):
    storage.delete_project(project_id)
    flash("Project deleted successfully", "success")
    return redirect(url_for("projects.list_projects"))

@projects_bp.route("/projects/edit/<int:project_id>", methods=["GET", "POST"])
def edit_project(project_id):
    project = storage.get_project(project_id)
    if not project:
        flash("Project not found", "error")
        return redirect(url_for("projects.list_projects"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        if not name:
            flash("Project name is required", "error")
        else:
            storage.update_project(project_id, name, description)
            flash("Project updated successfully", "success")
            return redirect(url_for("projects.list_projects"))

    return render_template("edit_project.html", project=project)

@projects_bp.route("/projects/<int:project_id>/stories/add", methods=["POST"])
def add_story(project_id):
    """Add a single story to a project (form POST)."""
    text = request.form.get("story") or request.form.get("text")
    if not text or not text.strip():
        flash("Story text is required", "error")
        return redirect(url_for("projects.view_project", project_id=project_id))

    storage.insert_story(project_id, text.strip())
    flash("Story added successfully", "success")
    return redirect(url_for("projects.view_project", project_id=project_id))

# Edit story
@projects_bp.route("/projects/<int:project_id>/stories/edit/<int:story_id>", methods=["GET", "POST"])
def edit_story(project_id, story_id):
    story = storage.get_story(story_id)
    if request.method == "POST":
        new_text = request.form.get("text")
        if new_text:
            storage.update_story(story_id, new_text)
            flash("Story updated successfully", "success")
            return redirect(url_for("projects.view_project", project_id=project_id))
    return render_template("edit_story.html", project_id=project_id, story=story)


# Bulk upload
@projects_bp.route("/projects/<int:project_id>/stories/bulk", methods=["GET", "POST"])
def bulk_upload_stories(project_id):
    if request.method == "POST":
        # Option 1: textarea input
        raw_stories = request.form.get("stories_bulk")
        if raw_stories:
            stories = raw_stories.splitlines()
            storage.insert_stories_bulk(project_id, stories)
            flash(f"{len(stories)} stories uploaded successfully", "success")
            return redirect(url_for("projects.view_project", project_id=project_id))

        # Option 2: file upload
        file = request.files.get("file")
        if file and file.filename.endswith(".txt"):
            stories = file.read().decode("utf-8").splitlines()
            storage.insert_stories_bulk(project_id, stories)
            flash(f"{len(stories)} stories uploaded from file", "success")
            return redirect(url_for("projects.view_project", project_id=project_id))

    return render_template("bulk_upload.html", project_id=project_id)


@projects_bp.route("/projects/<int:project_id>", methods=["GET", "POST"])
def view_project(project_id):
    project = storage.get_project(project_id)
    if not project:
        flash("Project not found", "error")
        return redirect(url_for("projects.list_projects"))

    if request.method == "POST":
        text = request.form.get("text")
        if not text:
            flash("Story text is required", "error")
        else:
            storage.insert_story(project_id, text)
            flash("Story added successfully", "success")
        return redirect(url_for("projects.view_project", project_id=project_id))

    stories = storage.get_stories_for_project(project_id)
    batches = storage.get_batches_of_project(project_id)
    return render_template("view_project.html", project=project, stories=stories, batches=batches)


@projects_bp.route("/projects/<int:project_id>/stories/delete/<int:story_id>", methods=["POST"])
def delete_story(project_id, story_id):
    storage.delete_story(story_id)
    flash("Story deleted successfully", "success")
    return redirect(url_for("projects.view_project", project_id=project_id))

@projects_bp.route("/projects/<int:project_id>/batches", methods=["GET", "POST"])
def manage_batches(project_id):
    if request.method == "POST":
        batch_name = request.form.get("batch_name")
        if batch_name:
            storage.create_batch(project_id, batch_name)
    batches = storage.get_batches_of_project(project_id)
    return render_template("batches.html", batches=batches, project_id=project_id)

@projects_bp.route("/projects/<int:project_id>/batches/create", methods=["GET", "POST"])
def create_batch_with_stories(project_id):
    stories = storage.get_stories_for_project(project_id)  # get all stories for this project
    if request.method == "POST":
        batch_name = request.form.get("batch_name")
        selected_story_ids = request.form.getlist("story_ids")  # checkboxes return list
        if batch_name and selected_story_ids:
            batch_id = storage.create_batch(project_id, batch_name)
            storage.assign_stories_to_batch(batch_id, [int(sid) for sid in selected_story_ids])
            flash(f"Batch '{batch_name}' created with {len(selected_story_ids)} stories.", "success")
            return redirect(url_for("projects.manage_batches", project_id=project_id))
    return render_template("create_batch.html", stories=stories, project_id=project_id)


@projects_bp.route("/batches/<int:batch_id>")
def view_batch(batch_id):
    batch = storage.get_batch(batch_id)  # fetch batch info
    stories = storage.get_stories_in_batch(batch_id)  # fetch stories in this batch
    if not batch:
        flash("Batch not found", "error")
        return redirect(url_for("projects.list_projects"))
    return render_template("view_batch.html", batch=batch, stories=stories)

@projects_bp.route("/batches/<int:batch_id>/evaluate", methods=["POST"])
def evaluate_batch(batch_id):
    stories = storage.get_stories_in_batch(batch_id)
    results = []
    for story in stories:
        # Call your existing evaluation logic
        outcome = evaluator.evaluate_story(story['text'])
        storage.insert_evaluation(story['id'], outcome)  # store evaluation
        results.append(outcome)
    flash(f"Batch evaluation completed for {len(stories)} stories.", "success")
    return redirect(url_for("projects.view_batch", batch_id=batch_id))

@projects_bp.route("/batches/<int:batch_id>/edit", methods=["GET", "POST"])
def edit_batch(batch_id):
    batch = storage.get_batch(batch_id)
    if not batch:
        flash("Batch not found", "error")
        return redirect(url_for("projects.list_projects"))

    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            flash("Batch name is required", "error")
        else:
            storage.update_batch(batch_id, name)
            flash("Batch updated successfully", "success")
            return redirect(url_for("projects.view_batch", batch_id=batch_id))

    return render_template("edit_batch.html", batch=batch)

@projects_bp.route("/batches/<int:batch_id>/delete", methods=["POST"])
def delete_batch(batch_id):
    storage.delete_batch(batch_id)
    flash("Batch deleted successfully", "success")
    # Redirect to the project page it belongs to
    batch = storage.get_batch(batch_id)
    project_id = batch['project_id'] if batch else None
    return redirect(url_for("projects.view_project", project_id=project_id or 0))



