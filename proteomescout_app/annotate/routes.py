"""
Dataset Annotation Routes

Provides endpoints for annotating user-uploaded phosphoproteomic datasets using
ProteomeScoutAPI.  The user uploads a CSV/TSV, selects the accession and peptide
columns, chooses annotation options, and downloads the annotated output.
"""
import io
import logging
import os

import pandas as pd
from flask import current_app, jsonify, render_template, request, Response

from proteomescout_app.annotate import bp

logger = logging.getLogger(__name__)

# Max upload size enforced server-side (separate from Flask MAX_CONTENT_LENGTH)
_MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


def _read_dataframe(file_obj):
    """Read an uploaded file-like object into a DataFrame.

    Sniffs the delimiter from the filename extension or raw bytes.
    Raises ValueError / pandas errors on malformed content.
    """
    raw = file_obj.read(_MAX_UPLOAD_BYTES)
    filename = getattr(file_obj, 'filename', '') or ''
    if filename.lower().endswith(('.tsv', '.txt')):
        sep = '\t'
    else:
        # Heuristic: whichever delimiter appears more in the first 4 KB wins
        sample = raw[:4096].decode('utf-8', errors='replace')
        sep = '\t' if sample.count('\t') >= sample.count(',') else ','
    return pd.read_csv(io.BytesIO(raw), sep=sep)


def _configure_api_data_dir():
    """Point proteomeScoutAPI at the data directory configured in the app."""
    import proteomeScoutAPI.config as pscout_config
    data_dir = current_app.config.get(
        'PROTEOMESCOUT_API_DATA_DIR',
        current_app.config.get('DATA_ROOT_DIR', 'data'),
    )
    pscout_config.DATASET_DIR = os.path.abspath(data_dir)


@bp.route('/')
def landing():
    return render_template('annotate/landing.html')


@bp.route('/get-columns', methods=['POST'])
def get_columns():
    """AJAX endpoint: parse an uploaded file and return its column names."""
    file = request.files.get('datasetFile')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided.'}), 400
    try:
        df = _read_dataframe(file)
        return jsonify({'columns': df.columns.tolist()})
    except Exception as exc:
        logger.warning('get_columns parse error: %s', exc)
        return jsonify({'error': f'Could not parse file: {exc}'}), 400


@bp.route('/run', methods=['POST'])
def run_annotation():
    """Annotate the uploaded dataset and return the result as a CSV download."""
    from proteomeScoutAPI import ProteomicDataset

    file = request.files.get('datasetFile')
    if not file or not file.filename:
        return jsonify({'error': 'No file provided.'}), 400

    accession_col = (request.form.get('accessionCol') or '').strip()
    peptide_col = (request.form.get('peptideCol') or '').strip()
    find_site = request.form.get('findSite') == '1'
    go_terms = request.form.get('goTerms') == '1'

    if not accession_col or not peptide_col:
        return jsonify({'error': 'Accession and peptide column names are required.'}), 400

    try:
        df = _read_dataframe(file)
    except Exception as exc:
        logger.warning('run_annotation file parse error: %s', exc)
        return jsonify({'error': f'Could not parse file: {exc}'}), 400

    _configure_api_data_dir()

    try:
        dataset = ProteomicDataset(
            df,
            accession_col=accession_col,
            peptide_col=peptide_col,
            find_site=find_site,
            GO_terms=go_terms,
        )
        dataset.annotate_dataset()
    except KeyError as exc:
        return jsonify({'error': str(exc)}), 400
    except RuntimeError as exc:
        logger.error('ProteomeScoutAPI data error: %s', exc)
        return jsonify({'error': str(exc)}), 503
    except Exception as exc:
        logger.exception('Annotation failed unexpectedly')
        return jsonify({'error': f'Annotation failed: {exc}'}), 500

    out = io.StringIO()
    dataset.dataset.to_csv(out, index=False)

    original_name = file.filename or 'dataset'
    base = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
    download_name = f'{base}_annotated.csv'

    return Response(
        out.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{download_name}"',
        },
    )
