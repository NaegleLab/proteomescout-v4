from flask import Blueprint

bp = Blueprint('annotate', __name__, url_prefix='/annotate')

from proteomescout_app.annotate import routes  # noqa: E402,F401
