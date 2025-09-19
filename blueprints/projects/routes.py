from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import storage

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

@projects_bp.route("/projects/<int:project_id>")
def view_project(project_id):
    project = storage.get_project(project_id)
    if not project:
        flash("Project not found", "error")
        return redirect(url_for("projects.list_projects"))
    return render_template("project_detail.html", project=project)

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
