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
    get_maximal_coverage_accession,
    load_protein_data,
    get_species_options,
    parse_accessions,
    parse_activation_loops,
    ptm_in_activation_loop,
)

logger = logging.getLogger(__name__)

# Max upload size enforced server-side (separate from Flask MAX_CONTENT_LENGTH)
_MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB


def _is_truthy(value):
    if pd.isna(value):
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if 'not found' in text:
        return True
    return text in {'1', 'true', 't', 'yes', 'y'}


def _accession_not_found_mask(df: pd.DataFrame) -> pd.Series:
    """Identify rows where annotation reports accession lookup failure."""
    if 'PScout_Errors' in df.columns:
        return df['PScout_Errors'].apply(
            lambda value: bool(str(value).strip()) and any(
                token in str(value).strip().lower()
                for token in (
                    'accession not found in database',
                    'peptide not found in sequence',
                    'could not map accession',
                    'could not map peptide',
                )
            )
        )

    not_found_columns = []
    for column in df.columns:
        label = str(column).strip().lower()
        if ('accession' in label and 'not found' in label) or ('accession' in label and 'error' in label):
            not_found_columns.append(column)

    if not not_found_columns:
        return pd.Series([False] * len(df), index=df.index)

    mask = pd.Series([False] * len(df), index=df.index)
    for column in not_found_columns:
        mask = mask | df[column].apply(_is_truthy)
    return mask


def _remap_key(accession, peptide):
    acc = '' if pd.isna(accession) else str(accession).strip()
    pep = '' if pd.isna(peptide) else str(peptide).strip()
    return (acc, pep)


def _project_remapped_accessions(df: pd.DataFrame, accession_col: str, peptide_col: str, remap_by_key: dict) -> list[str]:
    projected = []
    for _, row in df.iterrows():
        original_accession = '' if pd.isna(row.get(accession_col)) else str(row.get(accession_col)).strip()
        key = _remap_key(row.get(accession_col), row.get(peptide_col))
        projected.append(remap_by_key.get(key, original_accession))
    return projected


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
    configured_path = current_app.config.get(
        'PROTEOMESCOUT_API_DATA_DIR',
        current_app.config.get('DATA_ROOT_DIR', 'data'),
    )

    # ProteomeScoutAPI expects DATASET_DIR to be the parent directory that
    # contains a "ProteomeScout_Dataset" folder.
    resolved = os.path.abspath(configured_path)
    if os.path.isfile(os.path.join(resolved, 'data.tsv')):
        resolved = os.path.dirname(resolved)

    pscout_config.DATASET_DIR = resolved
    # Disable automatic download/update checks — the dataset is pre-loaded in
    # the deployment environment and the filesystem may be read-only.
    pscout_config.UPDATE = False


@bp.route('/')
def landing():
    return render_template('annotate/processing.html')


@bp.route('/dataset-annotation')
def dataset_annotation():
    return render_template('annotate/landing.html', species_options=get_species_options())


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


def _resolve_annotation_duplicates(df: pd.DataFrame) -> list[str]:
    """Rename duplicate columns after API annotation while keeping annotation names intact.

    The annotation DataFrame is concatenated to the right of user columns, so for
    duplicate names the rightmost entry is the API-generated annotation value.
    We preserve that rightmost column name and rename earlier columns to
    '<name>_original', '<name>_original_2', etc.
    """
    columns = list(df.columns)
    name_to_positions = {}
    for idx, name in enumerate(columns):
        name_to_positions.setdefault(name, []).append(idx)

    warnings = []
    used_names = set(columns)
    for name, positions in name_to_positions.items():
        if len(positions) <= 1:
            continue

        # Keep the rightmost duplicate as the API annotation column.
        original_positions = positions[:-1]
        rename_targets = []
        for sequence, position in enumerate(original_positions, start=1):
            suffix = '' if sequence == 1 else f'_{sequence}'
            candidate = f'{name}_original{suffix}'
            while candidate in used_names:
                sequence += 1
                candidate = f'{name}_original_{sequence}'
            columns[position] = candidate
            used_names.add(candidate)
            rename_targets.append(candidate)

        if rename_targets:
            warnings.append(
                f"Column '{name}' already existed in the upload. Preserved original column(s) as "
                + ', '.join(f"'{target}'" for target in rename_targets)
                + "."
            )

    if warnings:
        df.columns = columns

    return warnings


def _normalize_spyc_prediction_columns(df: pd.DataFrame) -> list[str]:
    """Normalize SpY-C prediction values to consistent text labels.

    Converts numeric/bool predictions and legacy confidence labels to:
    - binder
    - nonbinder
    """

    def _normalize_value(value):
        if pd.isna(value):
            return value

        if isinstance(value, bool):
            return 'binder' if value else 'nonbinder'

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if value == 1:
                return 'binder'
            if value == 0:
                return 'nonbinder'
            return value

        text = str(value).strip()
        if not text:
            return text

        lowered = text.lower()
        if lowered in {'1', 'true', 't', 'yes'}:
            return 'binder'
        if lowered in {'0', 'false', 'f', 'no'}:
            return 'nonbinder'

        lowered = lowered.replace('-', ' ').replace('_', ' ')
        lowered = ' '.join(lowered.split())
        if lowered in {'confident binder', 'binder'}:
            return 'binder'
        if lowered in {'confident nonbinder', 'confident non binder', 'nonbinder', 'non binder'}:
            return 'nonbinder'

        return value

    normalized_columns = []
    for column in df.columns:
        column_label = str(column).lower()
        if 'spy-c' not in column_label and 'spy c' not in column_label:
            continue

        df[column] = df[column].apply(_normalize_value)
        normalized_columns.append(str(column))

    return normalized_columns


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
    find_site = True
    go_terms = True
    update_max_coverage = request.form.get('updateMaxCoverage', '1') == '1'
    coverage_species = (request.form.get('coverageSpecies') or '').strip()

    if not accession_col or not peptide_col:
        return jsonify({'error': 'Accession and peptide column names are required.'}), 400

    species_options = get_species_options()
    if update_max_coverage:
        if not coverage_species:
            return jsonify({'error': 'Please select a species when maximal coverage is enabled.'}), 400
        if coverage_species not in species_options:
            return jsonify({'error': f'Species "{coverage_species}" is not available in the ProteomeScout data.'}), 400

    try:
        df = _read_dataframe(file)
        df = df.reset_index(drop=True)
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
        return jsonify({'error': 'Annotation failed due to an internal error. Please contact the administrator.'}), 500

    if update_max_coverage:
        failed_mask = _accession_not_found_mask(dataset.dataset)
        remap_by_key = {}

        if failed_mask.any():
            failed_rows = dataset.dataset[failed_mask]
            if accession_col in failed_rows.columns and peptide_col in failed_rows.columns:
                failed_accessions = failed_rows[accession_col].tolist()
                failed_peptides = failed_rows[peptide_col].tolist()
                for original_accession, peptide in zip(failed_accessions, failed_peptides):
                    original = '' if pd.isna(original_accession) else str(original_accession).strip()
                    key = _remap_key(original_accession, peptide)
                    candidate = get_maximal_coverage_accession(coverage_species, peptide)
                    candidate = str(candidate or '').strip()
                    updated = candidate or original
                    reason = 'no_peptide_match_in_species'
                    if candidate and updated != original:
                        reason = 'updated_with_species_peptide_match'
                    elif candidate and updated == original:
                        reason = 'candidate_same_as_original'

                    if updated and updated != original:
                        remap_by_key[key] = updated

        remapped_accessions = _project_remapped_accessions(df, accession_col, peptide_col, remap_by_key)
        remapped_count = 0
        for original, remapped in zip(df[accession_col].tolist(), remapped_accessions):
            original_text = '' if pd.isna(original) else str(original).strip()
            if remapped != original_text:
                remapped_count += 1

        if remapped_count > 0:
            remap_df = df.copy()
            remap_df['UniProt for Maximal Coverage'] = remapped_accessions
            try:
                remap_dataset = ProteomicDataset(
                    remap_df,
                    accession_col='UniProt for Maximal Coverage',
                    peptide_col=peptide_col,
                    find_site=find_site,
                    GO_terms=go_terms,
                )
                remap_dataset.annotate_dataset()
                dataset = remap_dataset
                logger.info('Applied maximal coverage fallback to %s rows.', remapped_count)
            except Exception:
                logger.exception('Maximal coverage fallback re-annotation failed; keeping initial annotation results')
                dataset.dataset['UniProt for Maximal Coverage'] = _project_remapped_accessions(
                    dataset.dataset,
                    accession_col,
                    peptide_col,
                    remap_by_key,
                )
        else:
            dataset.dataset['UniProt for Maximal Coverage'] = _project_remapped_accessions(
                dataset.dataset,
                accession_col,
                peptide_col,
                remap_by_key,
            )

    conflict_warnings = _resolve_annotation_duplicates(dataset.dataset)
    if conflict_warnings:
        for msg in conflict_warnings:
            logger.info('Column conflict resolved: %s', msg)

    normalized_spyc_cols = _normalize_spyc_prediction_columns(dataset.dataset)
    if normalized_spyc_cols:
        logger.info('Normalized SpY-C prediction labels in columns: %s', ', '.join(normalized_spyc_cols))

    # Backfill legacy activation-loop flag only when API did not provide one.
    if (
        find_site
        and 'modification_sites' in dataset.dataset.columns
        and 'site_in_activation_loop' not in dataset.dataset.columns
    ):
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
    if normalized_spyc_cols:
        headers['X-SpYC-Normalized'] = ' | '.join(normalized_spyc_cols)

    return Response(out.getvalue(), mimetype='text/csv', headers=headers)
