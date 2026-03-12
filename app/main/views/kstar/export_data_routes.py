"""
KSTAR Data Export Routes Module

This module provides Flask route handlers for exporting KSTAR analysis data
in various formats. It supports exporting both activity and FPR data either
individually or together as a ZIP archive.
The exported data reflects the current state of the visualization, including
any filtering, sorting, and custom labeling that has been applied.
Routes:
    /plot/export: Export both activities and FPR data as a ZIP file
    /plot/export/<data_type>: Export a specific data type (activities or fpr)
"""

from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename   
import pandas as pd
import logging
from io import BytesIO
import zipfile
import json

from app.main.views.kstar import bp
from app.main.views.kstar.utils import create_error_response
from app.main.views.kstar.modules import validate_plot_parameters

logger = logging.getLogger(__name__)

@bp.route('/plot/export', methods=['POST'])
@validate_plot_parameters
def export_data():
    """
    Export both activities and FPR data as a ZIP file.
    
    Processes the current visualization data (already filtered and sorted),
    applies custom column labels if specified, and packages both datasets
    into a ZIP archive.
    Request Parameters:
        log_results: JSON string of current log-transformed activity data
        fpr_df: JSON string of current FPR data
        export_format: File format ('csv' or 'tsv')
        file_name: Optional custom filename prefix
        changeXLabel: Whether to use custom column labels
        customXLabels: JSON dictionary of column name mappings
    Returns:
        ZIP file attachment containing both datasets in the requested format
    """
    try:
        current_log_json = request.form.get('log_results')
        current_fpr_json = request.form.get('fpr_df')
        
        if not current_log_json or not current_fpr_json:
            raise ValueError("Current data missing. Please generate plot first.")
        
        # Load the current data
        log_results = pd.read_json(current_log_json)
        fpr_df = pd.read_json(current_fpr_json)
        
        export_format = request.form.get('export_format', 'csv').lower()
        if export_format not in ['csv', 'tsv']:
            export_format = 'csv'
            
        custom_filename = request.form.get('file_name', '').strip()
        zip_filename = f'{custom_filename}.zip' if custom_filename else 'KSTAR_data_export.zip'
        
        delimiter = ',' if export_format == 'csv' else '\t'
        
        # Apply custom column labels if provided
        change_x_label = request.form.get('changeXLabel') == 'true'
        if change_x_label:
            try:
                custom_labels = json.loads(request.form.get('customXLabels', '{}'))
                if custom_labels:
                    log_results = log_results.rename(columns=custom_labels)
                    fpr_df = fpr_df.rename(columns=custom_labels)
                    logger.info("Applied custom column labels for export")
            except Exception as e:
                logger.error("Error applying custom labels: %s", e)
        
        # Prepare data for export
        activities_buffer = BytesIO()
        fpr_buffer = BytesIO()
        
        activities_df = 10 ** (-log_results)  # Convert back from -log10
        activities_df.to_csv(activities_buffer, sep=delimiter)
        fpr_df.to_csv(fpr_buffer, sep=delimiter)
        
        # Create ZIP archive
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            activities_buffer.seek(0)
            activities_filename = 'activities' if not custom_filename else f'{custom_filename}_activities'
            zip_file.writestr(f'{activities_filename}.{export_format}', activities_buffer.getvalue())
            
            fpr_buffer.seek(0)
            fpr_filename = 'fpr' if not custom_filename else f'{custom_filename}_fpr'
            zip_file.writestr(f'{fpr_filename}.{export_format}', fpr_buffer.getvalue())
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        logger.error("Error in export_data: %s", e, exc_info=True)
        return jsonify(create_error_response(e)), 500

@bp.route('/plot/export/<data_type>', methods=['POST'])
@validate_plot_parameters
def export_specific_data(data_type):
    """
    Export a specific data type (activities or fpr) as CSV or TSV.
    
    Processes the current visualization data for the specified data type,
    applies custom column labels if provided, and delivers the file for download.
    For activity data, values are converted back from -log10 to original scale.
    
    Parameters:
        data_type: Type of data to export ('activities' or 'fpr') 
    Request Parameters:
        log_results: JSON string of current log-transformed activity data
        fpr_df: JSON string of current FPR data
        export_format: File format ('csv' or 'tsv')
        file_name: Optional custom filename prefix
        changeXLabel: Whether to use custom column labels
        customXLabels: JSON dictionary of column name mappings
    Returns:
        CSV or TSV file attachment with the requested data
    """
    try:
        current_log_json = request.form.get('log_results')
        current_fpr_json = request.form.get('fpr_df')
        
        if not current_log_json or not current_fpr_json:
            raise ValueError("Current data missing. Please generate plot first.")
        
        export_format = request.form.get('export_format', 'csv').lower()
        if export_format not in ['csv', 'tsv']:
            export_format = 'csv'
            
        custom_filename = request.form.get('file_name', '').strip()
        delimiter = ',' if export_format == 'csv' else '\t'
        
        # Process custom column labels
        change_x_label = request.form.get('changeXLabel') == 'true'
        custom_labels = {}
        if change_x_label:
            try:
                custom_labels = json.loads(request.form.get('customXLabels', '{}'))
                logger.info("Processing custom labels for export")
            except Exception as e:
                logger.error("Error parsing custom labels: %s", e)
        
        output = BytesIO()
        
        if data_type == 'activities':
            log_results = pd.read_json(current_log_json)
            
            if custom_labels:
                log_results = log_results.rename(columns=custom_labels)
                
            activities_df = 10 ** (-log_results)  # Convert back from -log10
            activities_df.to_csv(output, sep=delimiter)
            
            filename = f'{custom_filename}_{data_type}.{export_format}' if custom_filename else f'KSTAR_{data_type}.{export_format}'
                
        elif data_type == 'fpr':
            fpr_df = pd.read_json(current_fpr_json)
            
            if custom_labels:
                fpr_df = fpr_df.rename(columns=custom_labels)
                
            fpr_df.to_csv(output, sep=delimiter)
            
            filename = f'{custom_filename}_{data_type}.{export_format}' if custom_filename else f'KSTAR_{data_type}.{export_format}'
        else:
            raise ValueError(f"Invalid data type: {data_type}")
        
        output.seek(0)
        
        mime_type = 'text/csv' if export_format == 'csv' else 'text/tab-separated-values'
        
        return send_file(
            output,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error in export_{data_type}: %s", e, exc_info=True)
        return jsonify(create_error_response(e)), 500