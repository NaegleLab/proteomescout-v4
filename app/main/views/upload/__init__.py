from flask import Blueprint

bp = Blueprint('upload', __name__,
    template_folder='templates',
    static_folder='static')

from app.main.views.upload import start, configure, review, metadata, conditions, confirm
