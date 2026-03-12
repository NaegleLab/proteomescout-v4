from flask import Blueprint

bp = Blueprint('batch', __name__,
    template_folder='templates',
    static_folder='static')

from app.main.views.batch import batch_search