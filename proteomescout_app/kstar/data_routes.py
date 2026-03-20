"""
KSTAR Data Processing Routes Module

This module provides Flask route handlers for processing and validating KSTAR data files.
It serves as the initial data processing layer, validating uploaded files and extracting
metadata needed for visualization configuration.

Routes:
    /get_columns: Extract and validate column and kinase data from uploaded files
"""

from flask import request, jsonify
import pandas as pd
import logging
import os
import re

from proteomescout_app.kstar import bp
from proteomescout_app.kstar.utils import create_error_response
from proteomescout_app.kstar.modules import read_csv_file, validate_files, validate_dataframe_compatibility

logger = logging.getLogger(__name__)

ACTIVITIES_PATTERN = re.compile(r'^(?P<experiment>.+)_mann_whitney_activities\.tsv$', re.IGNORECASE)


@bp.route('/discover_file_sets', methods=['POST'])
def discover_file_sets():
    try:
        directory_path = (request.form.get('directoryPath') or '').strip()
        if not directory_path:
            return jsonify({'error': 'Please provide a directory path.'}), 400
        if not os.path.isdir(directory_path):
            return jsonify({'error': f'Not a directory: {directory_path}'}), 400

        experiments = []
        for filename in os.listdir(directory_path):
            match = ACTIVITIES_PATTERN.match(filename)
            if not match:
                continue

            experiment_name = match.group('experiment')
            activities_path = os.path.join(directory_path, f'{experiment_name}_mann_whitney_activities.tsv')
            fpr_path = os.path.join(directory_path, f'{experiment_name}_mann_whitney_fpr.tsv')
            binary_path = os.path.join(directory_path, f'{experiment_name}_binarized_experiment.tsv')

            if not os.path.isfile(activities_path) or not os.path.isfile(fpr_path):
                continue

            experiments.append(
                {
                    'experiment': experiment_name,
                    'activitiesPath': activities_path,
                    'fprPath': fpr_path,
                    'binaryEvidencePath': binary_path if os.path.isfile(binary_path) else None,
                }
            )

        experiments.sort(key=lambda item: item['experiment'].lower())
        return jsonify({'directory': directory_path, 'experiments': experiments})
    except Exception as e:
        logger.error('Error in discover_file_sets: %s', e)
        return jsonify(create_error_response(e)), 500

@bp.route('/get_columns', methods=['POST'])
@validate_files
def get_columns():
    """
    Extract columns and index values from uploaded activity and FPR files.
    
    This endpoint serves as the initial data validation step, ensuring that
    the uploaded files are properly formatted and compatible with each other.
    It returns metadata needed for UI configuration including available samples
    and kinases.
    
    Request Parameters:
        activitiesFile: CSV file containing kinase activity data
        fprFile: CSV file containing false positive rate (FPR) data
    
    Returns:
        JSON response containing:
        - columns: List of column names (samples)
        - kinases: List of row names (kinases)
        - shape: Dictionary with row and column counts
        
        If validation fails, returns an error message with status code 400.
        For other exceptions, returns an error response with status code 500.
    """
    try:
        activities_file = request.files.get('activitiesFile')
        fpr_file = request.files.get('fprFile')
        activities_path = (request.form.get('activitiesPath') or '').strip()
        fpr_path = (request.form.get('fprPath') or '').strip()

        if activities_file and fpr_file:
            logger.info("Processing uploaded files: %s, %s", activities_file.filename, fpr_file.filename)
            activities_source = activities_file
            fpr_source = fpr_file
        else:
            logger.info("Processing selected file paths: %s, %s", activities_path, fpr_path)
            activities_source = activities_path
            fpr_source = fpr_path
        
        activities_df = read_csv_file(activities_source)
        fpr_df = read_csv_file(fpr_source)
        
        compatibility_error = validate_dataframe_compatibility(activities_df, fpr_df)
        if compatibility_error:
            return jsonify({"error": compatibility_error}), 400
            
        return jsonify({
            "columns": activities_df.columns.tolist(),
            "kinases": activities_df.index.tolist(),
            "shape": {"rows": len(activities_df.index), "columns": len(activities_df.columns)}
        })
    except Exception as e:
        logger.error("Error in get_columns: %s", e)
        return jsonify(create_error_response(e)), 500