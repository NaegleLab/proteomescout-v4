from flask import Blueprint

# Create Blueprint for KSTAR module
bp = Blueprint('kstar', __name__,
    template_folder='templates',
    static_folder='static')

# Import views/routes to register them with the blueprint
from app.main.views.kstar import (
    modules,
    core_routes,
    data_routes,
    plot_routes,
    export_data_routes,
    plotting,
    clustering,
    data_processing,
    utils
)



