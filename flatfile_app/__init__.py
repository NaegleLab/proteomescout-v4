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

        software_tools = [
            {
                'name': 'ProteomeScout',
                'github_url': 'https://github.com/NaegleLab/ProteomeScout',
                'paper_url': 'https://pubmed.ncbi.nlm.nih.gov/25414335/',
                'citation': (
                    'Matlock MK, Holehouse AS, Naegle KM. ProteomeScout: a repository and analysis '
                    'resource for post-translational modifications and proteins. Nucleic Acids Res. '
                    '2015;43(Database issue):D521-D530. doi: 10.1093/nar/gku1154.'
                ),
            },
            {
                'name': 'ProteomeScoutAPI',
                'github_url': 'https://github.com/NaegleLab/ProteomeScoutAPI',
                'paper_url': 'https://pubmed.ncbi.nlm.nih.gov/26659599/',
                'citation': (
                    'Holehouse AS, Naegle KM. Reproducible Analysis of Post-Translational '
                    'Modifications in Proteomes--Application to Human Mutations. PLoS One. '
                    '2015;10(12):e0144692. doi: 10.1371/journal.pone.0144692.'
                ),
            },
            {
                'name': 'KSTAR',
                'github_url': 'https://github.com/NaegleLab/KSTAR',
                'docs_url': 'https://naeglelab.github.io/KSTAR/index.html',
                'paper_url': 'https://pubmed.ncbi.nlm.nih.gov/35879309/',
                'citation': (
                    'Crowl S, Jordan BT, Ahmed H, Ma CX, Naegle KM. KSTAR: An algorithm to predict '
                    'patient-specific kinase activities from phosphoproteomic data. Nat Commun. '
                    '2022;13(1):4283. doi: 10.1038/s41467-022-32017-5.'
                ),
            },
            {
                'name': 'CoDIAC',
                'github_url': 'https://github.com/NaegleLab/CoDIAC',
                'docs_url': 'https://naeglelab.github.io/CoDIAC/index.html',
                'paper_url': 'https://pubmed.ncbi.nlm.nih.gov/41252491/',
                'citation': (
                    'Kandoor A, Martinez G, Hitchcock JM, Angel S, Campbell L, Rizvi S, Naegle KM. '
                    'CoDIAC: A comprehensive approach for interaction analysis provides insights into '
                    'SH2 domain function and regulation. Sci Signal. 2025;18(913):eads8396. '
                    'doi: 10.1126/scisignal.ads8396.'
                ),
            },
            {
                'name': 'PTM-POSE',
                'github_url': 'https://github.com/NaegleLab/PTM-POSE',
                'docs_url': 'https://naeglelab.github.io/PTM-POSE/',
                'paper_url': 'https://pubmed.ncbi.nlm.nih.gov/40513562/',
                'citation': (
                    'Crowl S, Coleman MB, Chaphiv A, Jordan BT, Naegle KM. Systematic analysis '
                    'of the effects of splicing on the diversity of post-translational '
                    'modifications in protein isoforms using PTM-POSE. Cell Syst. '
                    '2025;16(7):101318. doi: 10.1016/j.cels.2025.101318.'
                ),
            },
            {
                'name': 'DANSy',
                'github_url': 'https://github.com/NaegleLab/DANSy',
                'docs_url': 'https://naeglelab.github.io/DANSy/',
                'paper_url': 'https://pubmed.ncbi.nlm.nih.gov/39677636/',
                'citation': (
                    'Shimpi AA, Naegle KM. Uncovering the domain language of protein functionality '
                    'and cell phenotypes using DANSy. bioRxiv [Preprint]. 2025 Jul 1:2024.12.04.626803. '
                    'doi: 10.1101/2024.12.04.626803.'
                ),
            },
            {
                'name': 'OpenEnsembles',
                'github_url': 'https://github.com/NaegleLab/OpenEnsembles',
                'docs_url': 'https://naeglelab.github.io/OpenEnsembles/index.html',
                'paper_url': 'http://jmlr.org/papers/v19/18-100.html',
                'citation': (
                    'Ronan T, Anastasio S, Qi Z, Tavares PHS, Sloutsky R, Naegle KM. '
                    'OpenEnsembles: A Python Resource for Ensemble Clustering. '
                    'J Mach Learn Res. 2018;19(26):1-6.'
                ),
            },
            {
                'name': 'ASPEN',
                'github_url': 'https://github.com/NaegleLab/ASPEN',
                'paper_url': 'https://pubmed.ncbi.nlm.nih.gov/31621582/',
                'citation': (
                    'Sloutsky R, Naegle KM. ASPEN, a methodology for reconstructing protein '
                    'evolution with improved accuracy using ensemble models. eLife. '
                    '2019;8:e47676. doi: 10.7554/eLife.47676.'
                ),
            },
        ]

        return render_template('downloads.html', files=files, software_tools=software_tools)

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