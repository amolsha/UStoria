from datetime import datetime
from flask import Flask, render_template

from models import storage
from blueprints.evaluation import evaluation_bp
from blueprints.dashboard import dashboard_bp
from blueprints.projects import projects_bp
# from blueprints.api import api_bp

def create_app():
    app = Flask(__name__)

    app.secret_key = "13579"

    storage.init_db()

    app.register_blueprint(evaluation_bp, url_prefix="/evaluation")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(projects_bp, url_prefix="/projects")
    # app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/evaluation")
    def evaluation():
        return render_template("evaluation.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.now().year}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)


