from flask import Blueprint

evaluation_bp = Blueprint('evaluation', __name__, template_folder='templates')

from . import routes