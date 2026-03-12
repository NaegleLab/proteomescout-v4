from app.main.views.info import bp
from flask import render_template, current_app
@bp.route('/')
def home():
    current_app.logger.info('Loading landing page')
    return render_template('proteomescout/landing/landing.html')