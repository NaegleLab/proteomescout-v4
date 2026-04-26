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
from proteomescout_app.protein_data import (
    load_protein_data,
    parse_accessions,
    parse_activation_loops,
    ptm_in_activation_loop,
)

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
    # Disable automatic download/update checks — the dataset is pre-loaded in
    # the deployment environment and the filesystem may be read-only.
    pscout_config.UPDATE = False


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


# Columns that annotate_dataset() will append to the DataFrame.
_ANNOTATION_COLUMNS = {
    'gene_name', 'domains', 'domain_architecture', 'GO_terms', 'PScout_Errors',
    'modification_sites', 'aligned_peps', 'documented_phosphosites',
    'site_in_domain', 'site_in_macro', 'site_in_activation_loop',
}


def _resolve_column_conflicts(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Rename any input columns that would clash with annotation output columns.

    Returns the (possibly renamed) DataFrame and a list of warning messages
    describing each rename so the caller can surface them to the user.
    """
    conflicts = _ANNOTATION_COLUMNS & set(df.columns)
    if not conflicts:
        return df, []

    rename_map = {col: f'{col}_original' for col in conflicts}
    warnings = [
        f"Column '{col}' already exists and has been renamed to '{rename_map[col]}' "
        f"to avoid overwriting your data."
        for col in sorted(conflicts)
    ]
    return df.rename(columns=rename_map), warnings


def _build_accession_loop_map():
    """Build a dict mapping each UniProt accession to its activation loop list."""
    acc_map = {}
    for protein in load_protein_data().values():
        loops = parse_activation_loops(protein.get('activation_loop', ''))
        if loops:
            for acc in parse_accessions(protein.get('accessions', '')):
                acc_map.setdefault(acc, loops)
    return acc_map


def _add_activation_loop_column(df, accession_col):
    """Add site_in_activation_loop column to *df* in-place.

    Each cell is a semicolon-separated string of '1'/'0' values aligned to
    the positions in the modification_sites column.
    """
    acc_loop_map = _build_accession_loop_map()

    def _compute(row):
        acc = str(row.get(accession_col, '') or '').strip()
        sites_str = str(row.get('modification_sites', '') or '')
        loops = acc_loop_map.get(acc, [])
        results = []
        for site in sites_str.split(';'):
            site = site.strip()
            if not site:
                continue
            try:
                pos = int(''.join(c for c in site if c.isdigit()))
                results.append('1' if ptm_in_activation_loop(pos, loops) else '0')
            except (ValueError, TypeError):
                results.append('0')
        return ';'.join(results)

    df['site_in_activation_loop'] = df.apply(_compute, axis=1)


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

    df, conflict_warnings = _resolve_column_conflicts(df)
    if conflict_warnings:
        for msg in conflict_warnings:
            logger.info('Column conflict resolved: %s', msg)

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
        return jsonify({'error': 'Annotation failed due to an internal error. Please contact the administrator.'}), 500

    if find_site and 'modification_sites' in dataset.dataset.columns:
        _add_activation_loop_column(dataset.dataset, accession_col)

    out = io.StringIO()
    dataset.dataset.to_csv(out, index=False)

    original_name = file.filename or 'dataset'
    base = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
    download_name = f'{base}_annotated.csv'

    headers = {
        'Content-Disposition': f'attachment; filename="{download_name}"',
    }
    if conflict_warnings:
        headers['X-Annotation-Warnings'] = ' | '.join(conflict_warnings)

    return Response(out.getvalue(), mimetype='text/csv', headers=headers)
