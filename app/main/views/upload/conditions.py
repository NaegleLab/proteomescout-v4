from flask import render_template, request, flash, redirect, url_for, json
from flask_login import current_user
from app.main.views.upload import bp
from app import db


from app.database import upload, experiment

def save_conditions(exp):
    cond_type_list = request.form.getlist('condition_type')
    cond_value_list = request.form.getlist('condition_text')
    exp.conditions = []
    for cond_type, cond_value in zip(cond_type_list, cond_value_list):
        exp.add_experiment_condition(cond_type, cond_value)
    db.session.commit()


def mark_status(db_session):
    db_session.stage='confirm'
    db.session.commit()

def previous_conditions(exp):
    prev_conditions = []
    for condition in exp.conditions:
        prev_conditions.append({'type' : condition.type, 'value': condition.value})
    return prev_conditions

@bp.route('/<session_id>/conditions', strict_slashes=False, methods=['GET', 'POST'])
def conditions(session_id):
    user = current_user if current_user.is_authenticated else None
    db_session = upload.get_session_by_id(session_id, user=user)
    exp = experiment.get_experiment_by_id(db_session.experiment_id, user, False)
    old_conditions = previous_conditions(exp)
    submitted = request.method == 'POST' and request.form.get('submit_button') == 'btn-continue'
    if submitted:
        save_conditions(exp)
        mark_status(db_session)
        return redirect(url_for('upload.confirm', session_id = session_id))
    return render_template(
        'proteomescout/upload/conditions.html',
        old_conditions = json.dumps(old_conditions)
    )