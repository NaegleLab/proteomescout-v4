from flask import render_template
from flask_login import current_user
from app.main.views.experiments import bp
from app.database import experiment
from app.config import strings


@bp.route('/<experiment_id>', strict_slashes=False)
def home(experiment_id):
    user = None
    if current_user.is_authenticated:
        user = current_user
    
    ptm_exp = experiment.get_experiment_by_id(experiment_id, user)
    
    return render_template(
        'proteomescout/experiments/home.html',
        title = strings.experiment_page_title % (ptm_exp.name),
        experiment=ptm_exp)
