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

from app.main.views.kstar import bp
from app.main.views.kstar.utils import create_error_response
from app.main.views.kstar.modules import read_csv_file, validate_files, validate_dataframe_compatibility

logger = logging.getLogger(__name__)

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
        logger.info("Processing files: %s, %s", activities_file.filename, fpr_file.filename)
        
        activities_df = read_csv_file(activities_file)
        fpr_df = read_csv_file(fpr_file)
        
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