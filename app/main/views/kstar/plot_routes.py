"""
KSTAR Plotting Routes Module

This module provides Flask route handlers for generating, updating, and exporting KSTAR dot plots
and integrated plots (with dendrograms). It processes input data files (activities and FPR),
applies filtering, sorting, and clustering based on user parameters, and renders
visualizations using Matplotlib.

Key features:
- Processing uploaded KSTAR activity and FPR CSV files
- Filtering kinases based on significance or manual selection
- Sorting kinases and samples (alphabetical, by activity, hierarchical clustering)
- Rendering dot plots with optional dendrograms for hierarchical clustering
- Exporting plots in various formats (PNG, PDF, SVG, etc.)
- Interactive updates based on user filtering/sorting selections

All routes handle errors by returning descriptive JSON responses.
"""

from flask import request, jsonify, send_file
import pandas as pd
import json
import logging
import matplotlib.pyplot as plt
from io import BytesIO

from app.main.views.kstar import bp
from app.main.views.kstar.utils import parse_bool, safe_json_loads, create_error_response, parse_comma_separated_list
from app.main.views.kstar.plotting import create_integrated_plot, create_dot_plot
from app.main.views.kstar.clustering import handle_clustering_for_plot
from app.main.views.kstar.data_processing import (
    process_activities_data,
    filter_significant_kinases,
    handle_kinase_filtering,
    handle_sample_filtering
)

from app.main.views.kstar.modules import (
    read_csv_file,
    extract_plot_params,
    extract_plot_settings,
    extract_dendrogram_settings,
    extract_custom_labels,
    apply_sorting,
    validate_files,
    validate_plot_parameters
)

logger = logging.getLogger(__name__)

@bp.route('/plot', methods=['POST'])
@validate_files
@validate_plot_parameters
def generate_plot():
    """
    Generate a custom dot plot or integrated plot from uploaded KSTAR data files.
    
    This endpoint handles the initial plot creation from uploaded activity and FPR files.
    It processes the raw data, applies filtering based on significance or manual selections,
    performs requested sorting or clustering, and creates the visualization.
    
    Request Parameters:
    - activitiesFile: CSV file containing kinase activity data
    - fprFile: CSV file containing FPR data
    - Various plot settings (colors, sizes, sorting options, etc.)
    
    Returns:
        JSON response containing:
        - plot: Base64-encoded plot image
        - log_results: JSON representation of the processed activity data
        - fpr_df: JSON representation of the processed FPR data
        - original_log_results: JSON of the unmodified activity data (for reset)
        - original_fpr_df: JSON of the unmodified FPR data (for reset)
        
        If an error occurs, returns an error JSON response with status code 500.
    """
    try:
        # Extract configuration parameters from the request
        plot_params = extract_plot_params()
        plot_settings = extract_plot_settings()
        sort_settings = {
            'kinases_mode': request.form.get('sortKinases', 'none'),
            'samples_mode': request.form.get('sortSamples', 'none')
        }
        
        # Extract dendrogram toggle settings
        dendrogram_settings = extract_dendrogram_settings()
        
        # Get the uploaded files
        activities_file = request.files.get('activitiesFile')
        fpr_file = request.files.get('fprFile')
        binary_evidence_file = request.files.get('binary_evidence')
        
        # Read the CSV data into dataframes
        activities_df = read_csv_file(activities_file)
        fpr_df = read_csv_file(fpr_file)
        binary_evidence_df = None  # Evidence functionality removed
        
        # Process the raw activities data (log transform, etc.)
        log_results = process_activities_data(activities_df)
        original_log_results = log_results.copy()
        original_fpr_df = fpr_df.copy()
        
        # Apply significance-based filtering if requested
        if parse_bool(request.form.get('restrictKinases', 'false')):
            log_results, fpr_df, binary_evidence_df = filter_significant_kinases(
                log_results, fpr_df, binary_evidence_df
            )
        
        # Apply manual kinase filtering if specified
        kinases_to_drop = parse_comma_separated_list(request.form.get('kinases_to_drop', ''))
        if kinases_to_drop:
            log_results = log_results.drop(index=kinases_to_drop, errors='ignore')
            fpr_df = fpr_df.drop(index=kinases_to_drop, errors='ignore')
            # Evidence filtering removed
        
        # Apply interactive kinase and sample filtering
        log_results, fpr_df, binary_evidence_df = handle_kinase_filtering(
            log_results, fpr_df, binary_evidence_df, request.form
        )
        log_results, fpr_df, binary_evidence_df = handle_sample_filtering(
            log_results, fpr_df, binary_evidence_df, request.form.get('manualSampleSelect', '')
        )
        
        # Apply sorting based on settings (alphabetical, activity level, etc.)
        log_results, fpr_df, binary_evidence_df = apply_sorting(log_results, fpr_df, binary_evidence_df, sort_settings)
        
        # Apply hierarchical clustering if requested, and get linkage matrices
        log_results, fpr_df, binary_evidence_df, row_linkage, col_linkage = handle_clustering_for_plot(
            log_results, fpr_df, binary_evidence_df, sort_settings, plot_params, dendrogram_settings
        )
        
        # Extract custom column labels if provided
        custom_xlabels = extract_custom_labels(log_results)
        use_integrated_plot = parse_bool(request.form.get('useIntegratedPlot', 'true'))
        
        # Create either an integrated plot (with dendrograms) or a simple dot plot
        if use_integrated_plot and (row_linkage is not None or col_linkage is not None):
            plot_img = create_integrated_plot(
                log_results, fpr_df, binary_evidence_df,
                row_linkage=row_linkage, col_linkage=col_linkage,
                binary_sig=(request.form.get('significantActivity', 'binary') == 'binary'),
                custom_xlabels=custom_xlabels, show_evidence=False,
                **plot_params, **plot_settings, **dendrogram_settings
            )
        else:
            plot_img = create_dot_plot(
                log_results, fpr_df, binary_evidence_df,
                binary_sig=(request.form.get('significantActivity', 'binary') == 'binary'),
                custom_xlabels=custom_xlabels, **plot_params, **plot_settings
            )
        
        # Return the plot and data as JSON
        return jsonify({
            "plot": plot_img,
            "log_results": log_results.to_json(),
            "fpr_df": fpr_df.to_json(),
            "original_log_results": original_log_results.to_json(),
            "original_fpr_df": original_fpr_df.to_json()
        })
    except Exception as e:
        logger.error("Error in generate_plot: %s", e, exc_info=True)
        return jsonify(create_error_response(e)), 500

@bp.route('/update_plot', methods=['POST'])
@validate_plot_parameters
def update_plot():
    """
    Update an existing plot based on new filtering, sorting, or visualization parameters.
    
    This endpoint is called when UI controls are adjusted for an existing plot.
    It reads the original data stored in the frontend form, applies the requested
    modifications, and returns an updated visualization without requiring new file uploads.
    
    Request Parameters:
    - original_log_results: JSON string of the original activity data
    - original_fpr_df: JSON string of the original FPR data
    - Various filtering and sorting parameters
    
    Returns:
        JSON response containing:
        - plot: Base64-encoded updated plot image
        - log_results: JSON representation of the modified activity data
        - fpr_df: JSON representation of the modified FPR data
        
        If an error occurs, returns an error JSON response with status code 500.
    """
    try:
        # Get the original data from the frontend form
        orig_log_json = request.form.get('original_log_results')
        orig_fpr_json = request.form.get('original_fpr_df')
        if not orig_log_json or not orig_fpr_json:
            raise ValueError("Original data missing. Please generate plot first.")
        
        # Parse JSON data back to DataFrames
        log_results = pd.read_json(orig_log_json)
        fpr_df = pd.read_json(orig_fpr_json)

        binary_evidence_df = None 
        
        # Extract plot configuration parameters
        plot_params = extract_plot_params()
        plot_settings = extract_plot_settings()
        binary_sig = (request.form.get('significantActivity', 'binary') == 'binary')
        dendrogram_settings = extract_dendrogram_settings()

        # Apply significance-based filtering if requested
        if parse_bool(request.form.get('restrictKinases', 'false')):
            log_results, fpr_df, binary_evidence_df = filter_significant_kinases(
                log_results, fpr_df, binary_evidence_df
            )
        
        # Apply kinase filtering (select or remove mode)
        kinase_edit_mode = request.form.get('manualKinaseEdit', 'none')
        selected_kinases = safe_json_loads(request.form.get('kinaseSelect', '[]'), [])
        if kinase_edit_mode == 'select' and selected_kinases:
            # Keep only the selected kinases
            log_results = log_results.loc[selected_kinases]
            fpr_df = fpr_df.loc[selected_kinases]
        elif kinase_edit_mode == 'remove' and selected_kinases:
            # Remove the selected kinases
            log_results = log_results.drop(selected_kinases, errors='ignore')
            fpr_df = fpr_df.drop(selected_kinases, errors='ignore')
        
        # Apply sample filtering
        selected_samples = safe_json_loads(request.form.get('sampleSelect', '[]'), [])
        if selected_samples:
            log_results = log_results[selected_samples]
            fpr_df = fpr_df[selected_samples]
        
        # Configure sorting settings
        sort_settings = {
            'kinases_mode': request.form.get('sortKinases', 'none'),
            'samples_mode': request.form.get('sortSamples', 'none')
        }
        
        # Apply non-hierarchical sorting using the common function
        log_results, fpr_df, _ = apply_sorting(log_results, fpr_df, None, sort_settings) # Pass None for binary_evidence_df if not modified by this sort

        # Apply hierarchical clustering if requested
        log_results, fpr_df, _, row_linkage, col_linkage = handle_clustering_for_plot(
            log_results, fpr_df, None, sort_settings, plot_params, dendrogram_settings # Pass None for binary_evidence_df
        )

        # Get custom column labels
        custom_xlabels = extract_custom_labels(log_results)
        
        # Determine whether to use integrated plot with dendrograms
        use_integrated_plot = parse_bool(request.form.get('useIntegratedPlot', 'true'))
        
        # Create either an integrated plot or a simple dot plot
        if use_integrated_plot and (row_linkage is not None or col_linkage is not None):
            plot_img = create_integrated_plot(
                log_results, fpr_df, None,
                row_linkage=row_linkage, col_linkage=col_linkage,
                binary_sig=binary_sig, custom_xlabels=custom_xlabels,
                show_evidence=False,
                **plot_params, **plot_settings, **dendrogram_settings
            )
        else:
            plot_img = create_dot_plot(
                log_results, fpr_df, binary_sig=binary_sig,
                custom_xlabels=custom_xlabels, **plot_params, **plot_settings
            )
        
        # Return the updated plot and data
        return jsonify({
            "plot": plot_img,
            "log_results": log_results.to_json(),
            "fpr_df": fpr_df.to_json()
        })
    except Exception as e:
        logger.error("Error in update_plot: %s", e, exc_info=True)
        return jsonify(create_error_response(e)), 500

@bp.route('/plot/download', methods=['POST'])
@validate_plot_parameters
def download_plot():
    """
    Generate a high-quality plot file for download in the specified format.
    Uses the exact same processed data that's currently displayed.
    """
    try:
        # Use the CURRENT processed data (what's actually displayed)
        # NOT the original data with re-applied processing
        current_log_json = request.form.get('log_results')  # Remove fallback to original
        current_fpr_json = request.form.get('fpr_df')       # Remove fallback to original
        
        if not current_log_json or not current_fpr_json:
            raise ValueError("Current plot data missing. Please generate plot first.")

        # Parse the EXACT data that's currently displayed
        log_results = pd.read_json(current_log_json)
        fpr_df = pd.read_json(current_fpr_json)

        # Extract plot configuration parameters
        plot_params = extract_plot_params()
        plot_settings = extract_plot_settings()
        binary_sig = (request.form.get('significantActivity', 'binary') == 'binary')
        download_format = request.form.get('download_format', 'png')
        file_name = request.form.get('file_name', 'KSTAR_dotplot')
        dendrogram_settings = extract_dendrogram_settings()
        use_integrated_plot = parse_bool(request.form.get('useIntegratedPlot', 'true'))

        # Configure sorting settings (only for clustering, not for re-sorting)
        sort_settings = {
            'kinases_mode': request.form.get('sortKinases', 'none'),
            'samples_mode': request.form.get('sortSamples', 'none')
        }

        # ONLY apply clustering if needed (don't re-filter or re-sort)
        # The data is already filtered and sorted as displayed
        log_results, fpr_df, _, row_linkage, col_linkage = handle_clustering_for_plot(
            log_results, fpr_df, None, sort_settings, plot_params, dendrogram_settings
        )

        # Get custom column labels
        custom_xlabels = extract_custom_labels(log_results)

        # Create the exact same plot as displayed
        if use_integrated_plot and (row_linkage is not None or col_linkage is not None):
            fig = create_integrated_plot(
                log_results, fpr_df,
                row_linkage=row_linkage,
                col_linkage=col_linkage,
                download=True,
                binary_sig=binary_sig,
                custom_xlabels=custom_xlabels,
                **plot_params, **plot_settings, **dendrogram_settings
            )
        else:
            fig = create_dot_plot(
                log_results, fpr_df,
                binary_sig=binary_sig,
                custom_xlabels=custom_xlabels,
                download=True,
                **plot_params, **plot_settings
            )

        # Save and return the file
        output = BytesIO()
        dpi = int(request.form.get('dpi', 300))
        bg_color = plot_params.get('background_color', '#ffffff')
        fig.savefig(output, format=download_format, dpi=dpi, bbox_inches='tight', facecolor=bg_color)
        plt.close(fig)
        output.seek(0)

        mime_types = {
            'png': 'image/png', 'jpg': 'image/jpeg', 'pdf': 'application/pdf',
            'svg': 'image/svg+xml', 'eps': 'application/postscript', 'tif': 'image/tiff'
        }

        return send_file(
            output,
            mimetype=mime_types.get(download_format, 'application/octet-stream'),
            as_attachment=True,
            download_name=f"{file_name}.{download_format}"
        )

    except Exception as e:
        logger.error("Error in download_plot: %s", e, exc_info=True)
        return jsonify(create_error_response(e)), 500