"""Routes for preparing phosphoproteomic datasets for KSTAR."""

from __future__ import annotations

import io
import logging
import os
import time
from collections import Counter

import numpy as np
import pandas as pd
import requests
from flask import Response, current_app, jsonify, render_template, request

from proteomescout_app.kstar import bp
from proteomescout_app.dataset_processing.accessions import automatic_id_conversion
from proteomescout_app.dataset_processing.accessions import identify_accession_type
from proteomescout_app.dataset_processing.accessions import identify_most_common_accession_type
from proteomescout_app.dataset_processing.peptides import (
    PeptideSequenceError,
    detect_annotation,
    detect_most_common_format,
    format_peptide_from_df,
)
from proteomescout_app.protein_data import get_maximal_coverage_accession, get_species_options

logger = logging.getLogger(__name__)

_MISSING_TOKENS = {
    '',
    'na',
    'n/a',
    'nan',
    'null',
    'none',
    'nd',
    'missing',
    '#name?',
    '#n/a',
    '#value!',
    '#div/0!',
    '#null!',
    '#num!',
    '#ref!',
    'inf',
    '-inf',
}


def _read_dataframe(file_obj):
    raw = file_obj.read()
    filename = getattr(file_obj, 'filename', '') or ''
    if filename.lower().endswith(('.tsv', '.txt')):
        sep = '\t'
    else:
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

    resolved = os.path.abspath(configured_path)
    if os.path.isfile(os.path.join(resolved, 'data.tsv')):
        resolved = os.path.dirname(resolved)

    pscout_config.DATASET_DIR = resolved
    pscout_config.UPDATE = False


def _is_numeric_or_nan(series):
    saw_numeric_value = False
    non_missing_count = 0
    numeric_count = 0

    for value in series.tolist():
        if pd.isna(value):
            continue

        if isinstance(value, str):
            normalized = value.strip()
            if normalized.lower() in _MISSING_TOKENS:
                continue
            normalized = normalized.replace(',', '')
        else:
            normalized = value

        non_missing_count += 1
        try:
            float(normalized)
            saw_numeric_value = True
            numeric_count += 1
        except (TypeError, ValueError):
            continue

    if not saw_numeric_value or non_missing_count == 0:
        return False

    # Allow columns that are predominantly numeric with sparse artifact values.
    return (numeric_count / non_missing_count) >= 0.9


def _sample_strings(series, limit=200):
    values = []
    for value in series.dropna().tolist():
        if len(values) >= limit:
            break
        text = str(value).strip()
        if text:
            values.append(text)
    return values


def _sanitize_excel_peptide_value(value):
    """Remove common Excel formula artifacts from peptide strings.

    Excel may serialize leading dashes as formula-like text such as
    ="---PEPTIDE". We strip the leading '=' and unwrap matching quotes.
    """
    if pd.isna(value):
        return value

    if not isinstance(value, str):
        return value

    text = value.strip()
    while text.startswith('='):
        text = text[1:].lstrip()

    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        text = text[1:-1]

    return text


def _normalize_padded_centered_peptide(value):
    """Normalize aligned peptides that use terminal padding characters.

    If a peptide is uppercase/aligned with terminal padding (`_`, `-`, `.`),
    lowercase the amino acid nearest the center position *before* trimming
    padding so the modification site is preserved.
    """
    if pd.isna(value):
        return value

    if not isinstance(value, str):
        return value

    text = _sanitize_excel_peptide_value(value)
    if not isinstance(text, str):
        return text

    pad_chars = {'_', '-', '.'}
    has_terminal_padding = bool(text) and (text[0] in pad_chars or text[-1] in pad_chars)
    if not has_terminal_padding:
        return text

    alpha_positions = [idx for idx, char in enumerate(text) if char.isalpha()]
    if not alpha_positions:
        return text.strip('_.-')

    alpha_chars = [text[idx] for idx in alpha_positions]
    is_all_uppercase_alpha = all(char.isupper() for char in alpha_chars)
    if is_all_uppercase_alpha:
        center = (len(text) - 1) / 2
        target_idx = min(alpha_positions, key=lambda idx: abs(idx - center))
        text_chars = list(text)
        text_chars[target_idx] = text_chars[target_idx].lower()
        text = ''.join(text_chars)

    return text.strip('_.-')


def _extract_primary_accession(value, id_sep=None):
    if pd.isna(value):
        return ''

    text = str(value).strip()
    if not text:
        return ''

    if id_sep and id_sep in text:
        return text.split(id_sep)[0].strip()

    for sep in (';', ','):
        if sep in text:
            return text.split(sep)[0].strip()

    return text


def _resolve_uniprot_redirect_accession(accession):
    """Resolve UniProt accession redirects and return updated accession if changed."""
    if not accession:
        return None

    url = f'https://rest.uniprot.org/uniprotkb/{accession}.json'
    try:
        response = requests.get(url, timeout=20, allow_redirects=True)
    except Exception:
        return None

    if not response.ok:
        return None

    try:
        payload = response.json()
    except Exception:
        return None

    updated = str(payload.get('primaryAccession', '')).strip()
    if updated and updated != accession:
        return updated

    if response.history:
        final_path = response.url.rsplit('/', 1)[-1]
        redirected = final_path.split('.', 1)[0].strip()
        if redirected and redirected != accession:
            return redirected

    return None


def _should_check_uniprot_redirect(accession):
    """Return True only for likely non-canonical accessions.

    Criteria:
    - Does not start with O, P, or Q
    - OR has isoform suffix like -1, -2, ...
    """
    if not accession:
        return False

    acc = str(accession).strip().upper()
    if not acc:
        return False

    if '-' in acc:
        parts = acc.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return True

    return not acc.startswith(('O', 'P', 'Q'))


def _apply_uniprot_redirect_updates(df, accession_col, accession_out_col, id_sep=None):
    """Update UniProt accessions based on UniProt redirect behavior.

    Adds a log column populated only for changed values:
    - Updated Uniprot ID
    """
    stats = {
        'candidate_rows': 0,
        'unique_candidates': 0,
        'updated_rows': 0,
        'updated_accessions': 0,
    }

    log_col = 'UniProt ID Update Log'
    if log_col not in df.columns:
        df[log_col] = ''

    if accession_col not in df.columns or accession_out_col not in df.columns:
        return df, stats

    cache = {}
    for idx, row in df.iterrows():
        source_acc = _extract_primary_accession(row.get(accession_col), id_sep=id_sep)
        if not source_acc:
            continue

        acc_type = identify_accession_type(source_acc)
        if acc_type not in {'UniProtKB', 'UniProtKB_AC-ID'}:
            continue

        if not _should_check_uniprot_redirect(source_acc):
            continue

        stats['candidate_rows'] += 1

        if source_acc not in cache:
            cache[source_acc] = _resolve_uniprot_redirect_accession(source_acc)

        updated_acc = cache[source_acc]
        if not updated_acc:
            continue

        df.at[idx, accession_out_col] = updated_acc
        previous = str(df.at[idx, log_col] or '').strip()
        df.at[idx, log_col] = '; '.join(value for value in [previous, 'Updated Uniprot ID'] if value)
        stats['updated_rows'] += 1

    stats['unique_candidates'] = len(cache)
    stats['updated_accessions'] = sum(1 for updated in cache.values() if updated)

    return df, stats


def _detect_accession_column(df):
    best_column = None
    best_score = -1.0
    best_type = None
    for column in df.columns:
        sample = _sample_strings(df[column], limit=100)
        if not sample:
            continue
        try:
            accession_type = Counter(
                identify_most_common_accession_type([value]) for value in sample
            ).most_common(1)[0][0]
        except Exception:
            accession_type = None
        score = 0.0
        if accession_type:
            score = 0.8
        if any(token in column.lower() for token in ('accession', 'uniprot', 'protein', 'gene', 'refseq', 'ensembl')):
            score += 0.2
        if score > best_score:
            best_score = score
            best_column = column
            best_type = accession_type
    return best_column, best_type, best_score if best_score >= 0 else None


def _detect_peptide_column(df):
    best_column = None
    best_score = -1.0
    best_format = None
    for column in df.columns:
        sample = [
            _normalize_padded_centered_peptide(value)
            for value in _sample_strings(df[column], limit=100)
        ]
        sample = [value for value in sample if isinstance(value, str) and value.strip()]
        if not sample:
            continue
        score = 0.0
        try:
            best_format = detect_most_common_format(sample)
            score = 0.9
        except PeptideSequenceError:
            best_format = None
        if any(token in column.lower() for token in ('peptide', 'sequence', 'site', 'phospho')):
            score += 0.1
        if score > best_score:
            best_score = score
            best_column = column
    return best_column, best_format, best_score if best_score >= 0 else None


def _detect_data_columns(df, exclude_columns):
    return [column for column in df.columns if column not in exclude_columns and _is_numeric_or_nan(df[column])]


def _detect_accession_separator(df, accession_col):
    if not accession_col or accession_col not in df.columns:
        return ''
    sample = _sample_strings(df[accession_col], limit=100)
    if any(';' in value for value in sample):
        return ';'
    if any(',' in value for value in sample):
        return ','
    return ''


def _detect_peptide_indicator(samples):
    counts = Counter()
    for peptide in samples:
        try:
            indicator, after = detect_annotation(peptide)
        except Exception:
            continue
        counts[(indicator, after)] += 1
    if not counts:
        return None, True
    (indicator, after), _ = counts.most_common(1)[0]
    return indicator, after


@bp.route('/dataset-prep')
def dataset_prep():
    return render_template('kstar/dataset_prep.html', species_options=get_species_options())


@bp.route('/dataset-prep/preview', methods=['POST'])
def dataset_prep_preview():
    file = request.files.get('datasetFile')
    if not file or not file.filename:
        return jsonify({'error': 'Please choose a CSV or TSV file.'}), 400

    try:
        df = _read_dataframe(file)
        df.columns = [str(column).strip() for column in df.columns]
    except Exception as exc:
        logger.exception('Dataset prep preview failed')
        return jsonify({'error': f'Could not inspect file: {exc}'}), 400

    accession_col, accession_type, accession_score = _detect_accession_column(df)
    peptide_col, peptide_format, peptide_score = _detect_peptide_column(df)
    data_columns = _detect_data_columns(df, {accession_col, peptide_col})
    accession_separator = _detect_accession_separator(df, accession_col)
    peptide_indicator = None
    peptide_after = True
    if peptide_col:
        peptide_indicator, peptide_after = _detect_peptide_indicator(_sample_strings(df[peptide_col]))

    warnings = []
    if not accession_col:
        warnings.append('No strong accession-column match was found. Please choose one manually.')
    if not peptide_col:
        warnings.append('No strong peptide-column match was found. Please choose one manually.')
    if not data_columns:
        warnings.append('No numeric-only data columns were detected.')

    return jsonify({
        'columns': df.columns.tolist(),
        'rowCount': int(df.shape[0]),
        'columnCount': int(df.shape[1]),
        'accessionColumn': accession_col,
        'accessionType': accession_type,
        'accessionScore': accession_score,
        'peptideColumn': peptide_col,
        'peptideFormat': peptide_format,
        'peptideScore': peptide_score,
        'peptideIndicator': peptide_indicator,
        'peptideAfter': peptide_after,
        'accessionSeparator': accession_separator,
        'dataColumns': data_columns,
        'warnings': warnings,
    })


@bp.route('/dataset-prep/run', methods=['POST'])
def dataset_prep_run():
    started_at = time.perf_counter()
    file = request.files.get('datasetFile')
    if not file or not file.filename:
        return jsonify({'error': 'Please choose a CSV or TSV file.'}), 400

    accession_col = (request.form.get('accessionCol') or '').strip()
    peptide_col = (request.form.get('peptideCol') or '').strip()
    if not accession_col or not peptide_col:
        return jsonify({'error': 'Please select both an accession column and a peptide column.'}), 400

    try:
        df = _read_dataframe(file)
        df.columns = [str(column).strip() for column in df.columns]
    except Exception as exc:
        logger.exception('Dataset prep read failed')
        return jsonify({'error': f'Could not parse file: {exc}'}), 400

    logger.info(
        'Dataset prep run started for %s with %s rows and %s columns.',
        file.filename,
        int(df.shape[0]),
        int(df.shape[1]),
    )

    if accession_col not in df.columns:
        return jsonify({'error': f'Accession column "{accession_col}" was not found in the uploaded file.'}), 400
    if peptide_col not in df.columns:
        return jsonify({'error': f'Peptide column "{peptide_col}" was not found in the uploaded file.'}), 400

    # Remove Excel-inserted '=' formula markers before peptide processing.
    df[peptide_col] = df[peptide_col].apply(_normalize_padded_centered_peptide)

    prefix_data_columns = request.form.get('prefixDataColumns', '1') == '1'
    selected_data_columns = request.form.getlist('dataColumns')
    rename_map = {}
    if prefix_data_columns:
        for column_name in selected_data_columns:
            if column_name in df.columns and not column_name.startswith('data:'):
                rename_map[column_name] = f'data:{column_name}'
        if rename_map:
            df = df.rename(columns=rename_map)

    accession_separator = (request.form.get('accessionSeparator') or '').strip() or None
    keep_isoforms = request.form.get('keepIsoforms', '0') == '1'
    remove_unmapped = request.form.get('removeUnmapped', '1') == '1'
    taxon_raw = (request.form.get('taxonId') or '9606').strip()
    try:
        taxon_id = int(taxon_raw)
    except ValueError:
        return jsonify({'error': 'Taxon ID must be numeric.'}), 400

    peptide_mode = (request.form.get('peptideMode') or 'auto').strip()
    peptide_format = (request.form.get('peptideFormat') or '').strip()
    peptide_indicator = (request.form.get('peptideIndicator') or '').strip() or None
    peptide_after = request.form.get('peptideAfter', '1') == '1'
    annotate_prepared = True
    update_max_coverage = request.form.get('updateMaxCoverage', '1') == '1'
    coverage_species = (request.form.get('coverageSpecies') or '').strip()

    species_options = get_species_options()
    if update_max_coverage:
        if not coverage_species:
            return jsonify({'error': 'Please select a species when maximal coverage is enabled.'}), 400
        if coverage_species not in species_options:
            return jsonify({'error': f'Species "{coverage_species}" is not available in the ProteomeScout data.'}), 400

    try:
        id_conversion_started = time.perf_counter()
        converted_df, missing_rows = automatic_id_conversion(
            df,
            accession_col=accession_col,
            taxonID=taxon_id,
            keep_isoform_info=keep_isoforms,
            remove_unmapped=remove_unmapped,
            id_sep=accession_separator,
        )
        logger.info(
            'Dataset prep ID conversion finished in %.2fs; %s rows remain, %s rows unmapped.',
            time.perf_counter() - id_conversion_started,
            int(converted_df.shape[0]),
            int(missing_rows.shape[0]),
        )

        if peptide_mode == 'auto':
            sample_peptides = _sample_strings(converted_df[peptide_col])
            if not peptide_format:
                peptide_format = detect_most_common_format(sample_peptides)
            if peptide_format == 'annotated' and not peptide_indicator:
                peptide_indicator, peptide_after = _detect_peptide_indicator(sample_peptides)

        if not peptide_format:
            return jsonify({'error': 'Could not determine a peptide format. Please select one manually.'}), 400
        if peptide_format == 'annotated' and not peptide_indicator:
            return jsonify({'error': 'Annotated peptide format requires an indicator value.'}), 400

        peptide_format_started = time.perf_counter()
        converted_df = format_peptide_from_df(
            converted_df,
            peptide_col,
            new_peptide_col='Formatted Peptide',
            autodetect=False,
            format=peptide_format,
            indicator=peptide_indicator,
            after=peptide_after,
        )
        logger.info(
            'Dataset prep peptide formatting finished in %.2fs.',
            time.perf_counter() - peptide_format_started,
        )

        if 'Accession' in converted_df.columns:
            converted_df = converted_df.rename(columns={'Accession': 'UniProt Accession'})

        if 'UniProt Accession' in converted_df.columns:
            redirect_started = time.perf_counter()
            converted_df, redirect_stats = _apply_uniprot_redirect_updates(
                converted_df,
                accession_col='UniProt Accession',
                accession_out_col='UniProt Accession',
                id_sep=accession_separator,
            )
            logger.info(
                'Dataset prep redirect checks finished in %.2fs; candidate rows=%s, unique accessions=%s, updated rows=%s, updated accessions=%s.',
                time.perf_counter() - redirect_started,
                redirect_stats['candidate_rows'],
                redirect_stats['unique_candidates'],
                redirect_stats['updated_rows'],
                redirect_stats['updated_accessions'],
            )

        from proteomeScoutAPI import ProteomicDataset
        from proteomescout_app.annotate.routes import (
            _accession_not_found_mask,
            _add_activation_loop_column,
            _normalize_spyc_prediction_columns,
            _project_remapped_accessions,
            _remap_key,
            _resolve_annotation_duplicates,
        )

        _configure_api_data_dir()

        accession_for_annotation = 'UniProt Accession' if 'UniProt Accession' in converted_df.columns else 'Accession'
        peptide_for_annotation = 'Formatted Peptide' if 'Formatted Peptide' in converted_df.columns else peptide_col

        if accession_for_annotation not in converted_df.columns:
            return jsonify({'error': 'Prepared dataset is missing an accession column for annotation.'}), 400
        if peptide_for_annotation not in converted_df.columns:
            return jsonify({'error': 'Prepared dataset is missing a peptide column for annotation.'}), 400

        annotation_started = time.perf_counter()
        dataset = ProteomicDataset(
            converted_df,
            accession_col=accession_for_annotation,
            peptide_col=peptide_for_annotation,
            find_site=True,
            GO_terms=True,
        )
        dataset.annotate_dataset()
        logger.info(
            'Dataset prep initial annotation finished in %.2fs.',
            time.perf_counter() - annotation_started,
        )

        if update_max_coverage:
            coverage_started = time.perf_counter()
            failed_mask = _accession_not_found_mask(dataset.dataset)
            remap_by_key = {}

            if failed_mask.any():
                failed_rows = dataset.dataset[failed_mask]
                if accession_for_annotation in failed_rows.columns and peptide_for_annotation in failed_rows.columns:
                    failed_accessions = failed_rows[accession_for_annotation].tolist()
                    failed_peptides = failed_rows[peptide_for_annotation].tolist()
                    for original_accession, peptide in zip(failed_accessions, failed_peptides):
                        original = '' if pd.isna(original_accession) else str(original_accession).strip()
                        candidate = get_maximal_coverage_accession(coverage_species, peptide)
                        candidate = str(candidate or '').strip()
                        updated = candidate or original
                        if updated and updated != original:
                            remap_by_key[_remap_key(original_accession, peptide)] = updated

            remapped_accessions = _project_remapped_accessions(
                converted_df,
                accession_for_annotation,
                peptide_for_annotation,
                remap_by_key,
            )
            remapped_count = 0
            for original, remapped in zip(converted_df[accession_for_annotation].tolist(), remapped_accessions):
                original_text = '' if pd.isna(original) else str(original).strip()
                if remapped != original_text:
                    remapped_count += 1

            if remapped_count > 0:
                remap_df = converted_df.copy()
                remap_df['UniProt for Maximal Coverage'] = remapped_accessions
                reannotation_started = time.perf_counter()
                remap_dataset = ProteomicDataset(
                    remap_df,
                    accession_col='UniProt for Maximal Coverage',
                    peptide_col=peptide_for_annotation,
                    find_site=True,
                    GO_terms=True,
                )
                remap_dataset.annotate_dataset()
                dataset = remap_dataset
                logger.info(
                    'Dataset prep maximal-coverage re-annotation finished in %.2fs for %s remapped rows.',
                    time.perf_counter() - reannotation_started,
                    remapped_count,
                )
            else:
                dataset.dataset['UniProt for Maximal Coverage'] = _project_remapped_accessions(
                    dataset.dataset,
                    accession_for_annotation,
                    peptide_for_annotation,
                    remap_by_key,
                )

            logger.info(
                'Dataset prep maximal-coverage phase finished in %.2fs with %s remapped rows.',
                time.perf_counter() - coverage_started,
                remapped_count,
            )

        _resolve_annotation_duplicates(dataset.dataset)
        _normalize_spyc_prediction_columns(dataset.dataset)
        if 'UniProt for Maximal Coverage' in dataset.dataset.columns and 'UniProt Accession' in dataset.dataset.columns:
            dataset.dataset['UniProt Accession'] = dataset.dataset['UniProt for Maximal Coverage']
            if 'UniProt ID Update Log' in dataset.dataset.columns:
                existing_log = dataset.dataset['UniProt ID Update Log'].fillna('').astype(str)
                dataset.dataset['UniProt ID Update Log'] = existing_log.apply(
                    lambda value: '; '.join(part for part in [value.strip(), 'Updated for maximal coverage'] if part)
                )
        if (
            'modification_sites' in dataset.dataset.columns
            and 'site_in_activation_loop' not in dataset.dataset.columns
        ):
            _add_activation_loop_column(dataset.dataset, accession_for_annotation)

        converted_df = dataset.dataset
    except PeptideSequenceError as exc:
        return jsonify({'error': f'Peptide formatting failed: {exc}'}), 400
    except Exception as exc:
        logger.exception('Dataset prep run failed')
        return jsonify({'error': f'Dataset preparation failed: {exc}'}), 500

    logger.info(
        'Dataset prep run completed in %.2fs with %s output rows and %s output columns.',
        time.perf_counter() - started_at,
        int(converted_df.shape[0]),
        int(converted_df.shape[1]),
    )

    out = io.StringIO()
    converted_df.to_csv(out, index=False)

    original_name = os.path.basename(file.filename or 'dataset')
    base = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
    download_name = f'{base}_kstar_prepared_annotated.csv'

    headers = {'Content-Disposition': f'attachment; filename="{download_name}"'}
    if rename_map:
        headers['X-Data-Columns-Renamed'] = ' | '.join(rename_map.values())
    if not missing_rows.empty:
        headers['X-Missing-Accessions'] = str(len(missing_rows))
    headers['X-Integrated-Annotation'] = '1'

    return Response(out.getvalue(), mimetype='text/csv', headers=headers)