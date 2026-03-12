from flask import render_template
from flask_login import current_user
from app.main.views.experiments import bp
from app.database import experiment
from app.config import strings

@bp.route('/<experiment_id>/subset')
def subset(experiment_id):
    user = current_user if current_user.is_authenticated else None
    exp = experiment.get_experiment_by_id(experiment_id, user)
    return render_template(
        'proteomescout/experiments/subset.html',
        title = strings.experiment_subset_page_title % (exp.name),
        experiment=exp,
        )