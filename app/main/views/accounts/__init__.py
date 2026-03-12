from flask import Blueprint

bp = Blueprint('account', __name__,
    template_folder='templates',
    static_folder='static')

from app.main.views.accounts import manage, my_experiments