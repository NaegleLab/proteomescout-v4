from app.main.views.experiments import bp
from app import db

from app.database import experiment
from flask import render_template
from flask_login import current_user
from app.config import strings


@bp.route('/')
def landing():
    user = None
    if current_user.is_authenticated:
        user = current_user

    all_exps = experiment.get_all_experiments(user, filter_compendia=False)
    # all_exps = db.session.query(experiment.Experiment).all()
    all_compendia = [exp for exp in all_exps if exp.type == 'compendia']
    experiment_tree = experiment.get_experiment_tree(user)
    return render_template(
        'proteomescout/experiments/landing.html',
        title = strings.experiments_page_title,
        compendia=all_compendia,
        experiments=experiment_tree)
