from flask import Blueprint

bp = Blueprint('compendia', __name__,
    template_folder='templates',
    static_folder='static')

import app.main.views.files.compendia  # Import the module where your routes are defined