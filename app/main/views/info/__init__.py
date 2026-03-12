from flask import Blueprint

bp = Blueprint('info', __name__)

from app.main.views.info import home

