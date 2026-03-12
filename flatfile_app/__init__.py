import os

from flask import Flask, render_template

from flatfile_app.config import Config


def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    from flatfile_app.proteins import bp as proteins_bp
    from flatfile_app.kstar import bp as kstar_bp

    app.register_blueprint(proteins_bp)
    app.register_blueprint(kstar_bp)

    @app.route('/')
    def index():
        return render_template(
            'home.html',
            documentation_url=app.config.get('DOCUMENTATION_URL', '#'),
        )

    return app