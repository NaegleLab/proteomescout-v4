"""
KSTAR Core Routes Module

This module provides the core Flask route handlers for the KSTAR application,
including the landing page and static file serving endpoints.

Routes:
    /: Main landing page for the KSTAR visualization tool
    /static/js/kstar_plotting/<path:filename>: Serves JavaScript files
    /static/css/kstar_plotting.css: Serves the CSS file for styling
"""

from flask import render_template, send_from_directory
import os
import logging

from app.main.views.kstar import bp

logger = logging.getLogger(__name__)

@bp.route('/', methods=['GET'])
def landing() -> str:
    """
    Render the KSTAR landing page. 
    Returns:
        Rendered HTML template for the landing page
    """
    return render_template('proteomescout/kstar/landing.html')

@bp.route('/static/js/kstar_plotting/<path:filename>')
def serve_kstar_js(filename):
    """
    Serve JavaScript files from the static/js/kstar_plotting directory.
    Parameters:
        filename: Path to the requested JavaScript file        
    Returns:
        Requested static JavaScript file
    """
    return send_from_directory(os.path.join(bp.static_folder, 'js', 'kstar_plotting'), filename)

@bp.route('/static/css/kstar_plotting.css')
def serve_kstar_css():
    """
    Serve the KSTAR plotting CSS file.  
    Returns:
        The KSTAR plotting CSS stylesheet
    """
    return send_from_directory(os.path.join(bp.static_folder, 'css'), 'kstar_plotting.css')