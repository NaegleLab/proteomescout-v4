from flask import Blueprint

bp = Blueprint('experiment', __name__,
    template_folder='templates',
    static_folder='static')

from app.main.views.experiments import landing, home, summary, go, pfam, scansite, browse, subset, download_experiment
