from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user
from app.main.views.upload import bp
from app import db
from app.config import strings

from app.database import upload, experiment

 

@bp.route('/<session_id>/confirm', strict_slashes=False, methods=['GET', 'POST'])
def confirm(session_id):
    user = current_user if current_user.is_authenticated else None
    db_session = upload.get_session_by_id(session_id, user=user)
    exp = experiment.get_experiment_by_id(db_session.experiment_id, user, False)


    
    




    return render_template(
        'proteomescout/upload/confirm.html',
        message = strings.experiment_upload_confirm_message,
        experiment = exp
    )