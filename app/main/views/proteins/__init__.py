from flask import Blueprint

bp = Blueprint('protein', __name__,
    template_folder='templates',
    static_folder='static')

from app.main.views.proteins import search, structure, data, summary, expression, go, modification
# from app.main.views.proteins import data, summary, expression, go, modification
