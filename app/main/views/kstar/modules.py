"""
KSTAR Plot Configuration Module

This module provides helper functions and decorators for KSTAR visualization processing.
It centralizes common configuration extraction, data transformation, and validation 
logic used across the plotting workflow.

Functions:
    read_csv_file: Reads and parses CSV/TSV data files with appropriate separators
    extract_plot_params: Extracts figure dimensions and font size from request
    extract_plot_settings: Extracts color settings for plot elements
    extract_dendrogram_settings: Extracts dendrogram display preferences
    extract_custom_labels: Processes custom column labels if provided
    apply_sorting: Applies requested sorting strategies to data frames
    
Decorators:
    validate_files: Ensures required files are present with valid extensions
    validate_plot_parameters: Validates numeric and color parameters
"""

from typing import Dict, Any
from flask import request, jsonify
import pandas as pd
import numpy as np
import json
import logging
from functools import wraps
import matplotlib.pyplot as plt
from io import BytesIO
import os

from app.main.views.kstar.plotting import create_integrated_plot, create_dot_plot
from app.main.views.kstar.clustering import handle_clustering_for_plot
from app.main.views.kstar.data_processing import (
    process_activities_data,
    filter_significant_kinases,
    handle_kinase_filtering,
    handle_sample_filtering,
    validate_dataframe_compatibility
)
from app.main.views.kstar.utils import (
    parse_bool,
    get_sep,
    parse_form_data,
    safe_json_loads,
    create_error_response,
    DEFAULT_COLORS,
    DEFAULT_PLOT_PARAMS,
    ALLOWED_FILE_EXTENSIONS,
    FormDataValidator,
    parse_comma_separated_list
)

logger = logging.getLogger(__name__)

# --- Helper functions ---
def read_csv_file(file) -> pd.DataFrame:
    """
    Read a CSV/TSV file using the appropriate separator and index column.
    
    Parameters:
        file: File object from request.files
        
    Returns:
        Pandas DataFrame with data and proper index
    """
    sep = get_sep(file.filename)
    try:
        return pd.read_csv(file, sep=sep, index_col=0)
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, nrows=5)
        if df.columns[0] == 'Unnamed: 0':
            file.seek(0)
            return pd.read_csv(file, index_col=0)
        return df

def extract_plot_params() -> Dict[str, Any]:
    """
    Extract figure dimensions and font size from request form.
    
    Returns:
        Dictionary with fig_width, fig_height, and fontsize parameters
    """
    return {
        'fig_width': parse_form_data(request.form, 'figureWidth', DEFAULT_PLOT_PARAMS['fig_width'], float),
        'fig_height': parse_form_data(request.form, 'figureHeight', DEFAULT_PLOT_PARAMS['fig_height'], float),
        'fontsize': parse_form_data(request.form, 'fontSize', DEFAULT_PLOT_PARAMS['fontsize'], float)
    }

def extract_plot_settings() -> Dict[str, Any]:
    """
    Extract color settings for plot elements from request form.
    
    Returns:
        Dictionary with background_color, activity_color, and other color settings
    """
    return {
        'background_color': request.form.get('backgroundColor', DEFAULT_COLORS['background']),
        'activity_color': request.form.get('activityColor', DEFAULT_COLORS['activity']),
        'noactivity_color': request.form.get('lackActivityColor', DEFAULT_COLORS['no_activity']),
        'kinases_dendrogram_color': request.form.get('kinases_dendrogram_color', '#000000'),
        'samples_dendrogram_color': request.form.get('samples_dendrogram_color', '#000000')  
    }

def extract_dendrogram_settings() -> Dict[str, bool]:
    """
    Extract dendrogram display preferences from request form.
    
    Returns:
        Dictionary with boolean flags for dendrogram display options
    """
    return {
        'show_kinases_dendrogram_inside': parse_bool(request.form.get('showKinasesDendrogramInside', 'false')),
        'show_samples_dendrogram': parse_bool(request.form.get('showSamplesDendrogram', 'true')),
    }

def extract_custom_labels(log_results: pd.DataFrame):
    """
    Process custom column labels if provided in the request.
    
    Parameters:
        log_results: DataFrame whose columns may need custom labels
        
    Returns:
        List of labels or None if no custom labels requested
    """
    if parse_bool(request.form.get('changeXLabel', 'false')):
        try:
            custom_labels = safe_json_loads(request.form.get('customXLabels', '{}'), {})
            return [custom_labels.get(col, col) for col in log_results.columns]
        except Exception as e:
            logger.warning("Error parsing custom labels: %s", e)
    return None

def apply_sorting(log_results: pd.DataFrame, fpr_df: pd.DataFrame, binary_evidence_df, sort_settings: Dict[str, str]):
    """
    Apply manual or activity-based sorting to the provided data frames.
    Samples can be sorted by a user-selected reference kinase.
    """
    
    # --- Step 1: Apply Kinase Sorting ---
    kinase_sort_mode = sort_settings.get('kinases_mode', 'none')
    logger.debug(f"Applying kinase sort mode: {kinase_sort_mode}")
    
    if kinase_sort_mode == 'manual':
        manual_order_json = request.form.get('manualKinaseOrder')
        if manual_order_json:
            try:
                manual_order = json.loads(manual_order_json)
                valid_manual_order = [k for k in manual_order if k in log_results.index]
                if valid_manual_order:
                    log_results = log_results.reindex(valid_manual_order)
                    fpr_df = fpr_df.reindex(valid_manual_order)
                    if binary_evidence_df is not None:
                        binary_evidence_df = binary_evidence_df.reindex(valid_manual_order)
            except json.JSONDecodeError:
                logger.error("Invalid manual kinase order JSON: %s", manual_order_json)
    elif kinase_sort_mode.startswith('by_activity_'):
        ascending_kinases = kinase_sort_mode.endswith('_asc')
        if not log_results.empty and log_results.shape[1] > 0:
            sort_by_kinase_col = log_results.columns[0]
            log_results = log_results.sort_values(by=sort_by_kinase_col, ascending=ascending_kinases)
            fpr_df = fpr_df.reindex(log_results.index)
            if binary_evidence_df is not None:
                binary_evidence_df = binary_evidence_df.reindex(log_results.index)

    # --- Step 2: Apply Sample Sorting ---
    sample_sort_mode = sort_settings.get('samples_mode', 'none')
    logger.debug(f"Applying sample sort mode: {sample_sort_mode}")
    
    if sample_sort_mode.startswith('by_selected_kinase_'): # e.g., 'by_selected_kinase_asc' or 'by_selected_kinase_desc'
        # Get the kinase name selected by the user from the form
        # We'll need to ensure the frontend sends this parameter.
        selected_ref_kinase = request.form.get('sample_sort_ref_kinase') 
        
        if not selected_ref_kinase:
            logger.warning("Sample sort mode is 'by_selected_kinase' but 'sample_sort_ref_kinase' parameter is missing. Skipping sample sort.")
        elif selected_ref_kinase not in log_results.index:
            logger.warning(
                f"Selected reference kinase '{selected_ref_kinase}' for sample sorting not found in data. "
                f"Available kinases: {list(log_results.index)}. Skipping sample sort."
            )
        elif not log_results.empty:
            ascending_samples = sample_sort_mode.endswith('_asc')
            
            logger.debug(f"Sample sorting by user-selected reference kinase: '{selected_ref_kinase}', ascending: {ascending_samples}")
            logger.debug(f"Values for '{selected_ref_kinase}': {log_results.loc[selected_ref_kinase].to_dict()}")
            
            original_cols = list(log_results.columns)
            sorted_cols_series = log_results.loc[selected_ref_kinase].sort_values(ascending=ascending_samples)
            sorted_cols = list(sorted_cols_series.index)
            
            if original_cols == sorted_cols:
                logger.debug(f"Sample order unchanged. Data for '{selected_ref_kinase}' might be uniform or already sorted.")
            else:
                logger.debug(f"Sample order changed. New order: {sorted_cols}")

            log_results = log_results[sorted_cols]
            fpr_df = fpr_df[sorted_cols]
            if binary_evidence_df is not None:
                binary_evidence_df = binary_evidence_df[sorted_cols]
        else:
            logger.debug("Sample sorting by selected kinase skipped: DataFrame is empty.")
            
    # Add other sample sort modes here if needed (e.g., 'by_clustering' if you re-implement it here)
            
    return log_results, fpr_df, binary_evidence_df

# --- Decorators ---
def validate_files(func):
    """
    Decorator to validate the presence and format of required uploaded files.
    
    Checks that both activities and FPR files are provided and have allowed extensions.
    
    Returns:
        Decorated function or error response
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        activities_file = request.files.get('activitiesFile')
        fpr_file = request.files.get('fprFile')
        if not activities_file or not fpr_file:
            return jsonify({"error": "Please provide both activities and FPR files."}), 400
        for file in [activities_file, fpr_file]:
            if not FormDataValidator.validate_file_extension(file.filename, ALLOWED_FILE_EXTENSIONS):
                return jsonify({
                    "error": f"Invalid file extension for {file.filename}. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
                }), 400
        return func(*args, **kwargs)
    return wrapper

def validate_plot_parameters(func):
    """
    Decorator to validate numeric and color values in plot parameters.
    
    Ensures figure dimensions are positive numbers and colors are valid hex codes.
    
    Returns:
        Decorated function or error response
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        for param in ['figureWidth', 'figureHeight', 'fontSize']:
            value = request.form.get(param)
            if value and not FormDataValidator.validate_numeric(value, min_val=0):
                return jsonify({"error": f"Invalid {param}: must be a positive number"}), 400
        for param in ['backgroundColor', 'activityColor', 'lackActivityColor']:
            color = request.form.get(param)
            if color and not FormDataValidator.validate_color_hex(color):
                return jsonify({"error": f"Invalid color format for {param}: {color}"}), 400
        return func(*args, **kwargs)
    return wrapper