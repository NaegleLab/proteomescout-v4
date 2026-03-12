import os

from flask import Flask, abort, render_template, send_file, url_for

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

    @app.route('/about')
    def about():
        return render_template(
            'about.html',
            documentation_url=app.config.get('DOCUMENTATION_URL', '#'),
            kstar_galaxy_url=(
                'https://usegalaxy.org/?tool_id=toolshed.g2.bx.psu.edu%2Frepos%2Fnaegle_lab%2F'
                'kstar_calculate%2Fkstar_calculate%2F1.1.0&version=latest'
            ),
            proteomescout_api_url='https://github.com/NaegleLab/ProteomeScoutAPI',
            naegle_lab_url=app.config.get('NAEGLE_LAB_URL', '#'),
        )

    @app.route('/downloads')
    def downloads():
        files = []
        for key, label, description in (
            ('PROTEIN_DATA_TSV_PATH', 'Protein data TSV', 'Primary flat-file protein/PTM dataset.'),
            ('CITATIONS_TSV_PATH', 'Citation TSV', 'Evidence and citation records linked from PTM entries.'),
        ):
            file_path = app.config.get(key)
            exists = bool(file_path) and os.path.isfile(file_path)
            files.append(
                {
                    'label': label,
                    'description': description,
                    'path': file_path,
                    'exists': exists,
                    'size': os.path.getsize(file_path) if exists else None,
                    'download_url': url_for('download_file', file_key=key) if exists else None,
                }
            )

        return render_template('downloads.html', files=files)

    @app.route('/downloads/<file_key>')
    def download_file(file_key):
        allowed_keys = {'PROTEIN_DATA_TSV_PATH', 'CITATIONS_TSV_PATH'}
        if file_key not in allowed_keys:
            abort(404)

        file_path = app.config.get(file_key)
        if not file_path or not os.path.isfile(file_path):
            abort(404)

        return send_file(file_path, as_attachment=True, download_name=os.path.basename(file_path))

    return app