"""
KSTAR Utilities Module

This module provides helper functions and classes used throughout the KSTAR 
application. It includes utilities for form data parsing, JSON handling, 
validation, error formatting, and file operations.

Functions:
    parse_bool: Convert string representations to boolean values
    get_sep: Determine file separator based on extension
    safe_json_loads: Safely parse JSON with fallback to default value
    parse_form_data: Extract and parse form values with type conversion
    sanitize_filename: Remove path components from filenames
    parse_comma_separated_list: Convert comma-separated strings to lists
    encode_image_base64: Convert image data to base64 strings
    create_error_response: Generate standardized error response dictionaries

Classes:
    FormDataValidator: Utility class for validating form inputs
"""

from typing import Union, Dict, Any, List, Optional, Callable
import json
import traceback
import base64
from io import BytesIO

def parse_bool(val: Union[str, bool]) -> bool:
    """Parse a boolean value from a string or boolean input."""
    return val if isinstance(val, bool) else str(val).lower() == 'true'

def get_sep(filename: str) -> str:
    """Return '\t' if the file is a TSV, otherwise ','."""
    return '\t' if filename.lower().endswith('.tsv') else ','

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load a JSON string, returning default if parsing fails."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def parse_form_data(
    form_data: Dict[str, Any],
    key: str,
    default: Any = None,
    parser: Optional[Callable[[Any], Any]] = None
) -> Any:
    """
    Retrieve and optionally parse a form value.
    
    If the key is missing or parsing fails, return the default.
    """
    value = form_data.get(key, default)
    if value is None or parser is None:
        return value
    try:
        return parser(value)
    except (ValueError, TypeError):
        return default

def sanitize_filename(filename: str) -> str:
    """
    Remove any path components from the filename to prevent directory traversal.
    """
    return filename.replace("\\", "/").split("/")[-1]

def parse_comma_separated_list(value: str) -> List[str]:
    """
    Split a comma-separated string into a list of non-empty, trimmed strings.
    """
    return [s.strip() for s in value.split(',') if s.strip()]

def encode_image_base64(image_data: BytesIO) -> str:
    """
    Encode the content of a BytesIO image to a base64 string.
    """
    image_data.seek(0)
    return base64.b64encode(image_data.getvalue()).decode('utf-8')

def create_error_response(error: Exception) -> Dict[str, str]:
    """
    Create a standardized error response dictionary.
    """
    return {"error": str(error), "traceback": traceback.format_exc()}

class FormDataValidator:
    """Utility class for validating form inputs."""

    @staticmethod
    def validate_numeric(value: str,
                         min_val: Optional[float] = None,
                         max_val: Optional[float] = None) -> bool:
        """
        Check if a string represents a numeric value within an optional range.
        """
        try:
            num = float(value)
            return (min_val is None or num >= min_val) and (max_val is None or num <= max_val)
        except ValueError:
            return False

    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """
        Check if a filename ends with one of the allowed extensions.
        """
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)

    @staticmethod
    def validate_color_hex(color: str) -> bool:
        """
        Validate that the string is a proper hex color (in #RGB or #RRGGBB format).
        """
        if not (color.startswith('#') and len(color) in (4, 7)):
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False

# Constants used across the application
ALLOWED_FILE_EXTENSIONS = ['.csv', '.tsv']
DEFAULT_COLORS = {
    'background': '#FFFFFF',
    'activity': '#FF3300',
    'no_activity': '#6b838f'
}
DEFAULT_PLOT_PARAMS = {
    'fig_width': 4,
    'fig_height': 10,
    'fontsize': 10,
    'use_integrated_plot': True
}
