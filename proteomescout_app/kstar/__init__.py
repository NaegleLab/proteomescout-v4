from flask import Blueprint, render_template


bp = Blueprint('kstar', __name__, url_prefix='/kstar')


@bp.route('/')
def landing():
    return render_template('kstar/landing.html')


from proteomescout_app.kstar import data_routes, export_data_routes, plot_routes  # noqa: E402,F401