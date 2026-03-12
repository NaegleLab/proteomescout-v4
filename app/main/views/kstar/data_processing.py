"""
KSTAR Data Processing Module

This module provides functions for processing, validating, filtering, and sorting
KSTAR analysis data. It handles operations on kinase activity, FPR, and optional
binary evidence dataframes.

Functions:
    validate_dataframe_compatibility: Ensures dataframes have compatible indices and columns
    process_activities_data: Prepares raw activity values for visualization
    filter_significant_kinases: Filters kinases based on significance thresholds
    handle_kinase_filtering: Applies manual kinase selection or removal
    handle_sample_filtering: Filters samples based on user selections
    sort_by_activity: Sorts kinases or samples based on activity levels
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, List, Any, Optional
from .utils import safe_json_loads, parse_comma_separated_list

logger = logging.getLogger(__name__)

def validate_dataframe_compatibility(
    activities_df: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df: Optional[pd.DataFrame] = None
) -> Optional[str]:
    """
    Validate that DataFrames have compatible indices and columns.
    Parameters:
        activities_df: DataFrame with kinase activity data
        fpr_df: DataFrame with FPR values
        binary_evidence_df: Optional evidence DataFrame
    Returns:
        None if compatible, error message string if incompatible
    """
    try:
        if not set(activities_df.index) <= set(fpr_df.index):
            return "Activities file contains kinases not found in FPR file."
        if not set(activities_df.columns) <= set(fpr_df.columns):
            return "Activities file contains samples not found in FPR file."
        if binary_evidence_df is not None:
            if not set(activities_df.index) <= set(binary_evidence_df.index):
                return "Activities file contains kinases not found in binary evidence file."
            if not set(activities_df.columns) <= set(binary_evidence_df.columns):
                return "Activities file contains samples not found in binary evidence file."
        return None
    except Exception as e:
        logger.error("Error validating DataFrame compatibility: %s", e)
        return str(e)

def process_activities_data(activities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare activities data by replacing zeros with NaN and computing -log10.
    Parameters:
        activities_df: DataFrame with raw kinase activity data
    Returns:
        Processed DataFrame with -log10 transformed values
    """
    if activities_df.empty:
        raise ValueError("Empty activities DataFrame provided")
    try:
        activities_df = activities_df.replace(0, np.nan)
        if (activities_df < 0).any().any():
            raise ValueError("Activities DataFrame contains negative values")
        return -np.log10(activities_df)
    except Exception as e:
        logger.error("Error processing activities data: %s", e)
        raise

def filter_significant_kinases(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df: Optional[pd.DataFrame] = None,
    threshold: float = 0.05
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Filter kinases based on whether any FPR values are below the significance threshold.
    Parameters:
        log_results: DataFrame with log-transformed activity data
        fpr_df: DataFrame with FPR values
        binary_evidence_df: Optional evidence DataFrame
        threshold: FPR significance cutoff (default: 0.05)
    Returns:
        Tuple of filtered DataFrames (log_results, fpr_df, binary_evidence_df)
    """
    try:
        sig_mask = (fpr_df < threshold).any(axis=1)
        filtered_binary = binary_evidence_df[sig_mask] if binary_evidence_df is not None else None
        return log_results[sig_mask], fpr_df[sig_mask], filtered_binary
    except Exception as e:
        logger.error("Error filtering significant kinases: %s", e)
        raise

def handle_kinase_filtering(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df: Optional[pd.DataFrame],
    form_data: Dict[str, Any]
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Filter kinases based on manual selection/removal and a legacy comma-separated drop list.
    Parameters:
        log_results: DataFrame with log-transformed activity data
        fpr_df: DataFrame with FPR values
        binary_evidence_df: Optional evidence DataFrame
        form_data: Dictionary containing filter parameters
    Returns:
        Tuple of filtered DataFrames (log_results, fpr_df, binary_evidence_df)
    """
    try:
        manual_mode = form_data.get('kinaseEditMode', 'none')
        if manual_mode != 'none':
            selected = safe_json_loads(form_data.get('kinaseSelect', '[]'), [])
            if selected:
                if manual_mode == 'select':
                    indexer = lambda df: df.loc[selected]
                elif manual_mode == 'remove':
                    indexer = lambda df: df.drop(index=selected, errors='ignore')
                log_results = indexer(log_results)
                fpr_df = indexer(fpr_df)
                if binary_evidence_df is not None:
                    binary_evidence_df = indexer(binary_evidence_df)
        kinases_to_drop = parse_comma_separated_list(form_data.get('kinases_to_drop', ''))
        if kinases_to_drop:
            dropper = lambda df: df.drop(index=kinases_to_drop, errors='ignore')
            log_results = dropper(log_results)
            fpr_df = dropper(fpr_df)
            if binary_evidence_df is not None:
                binary_evidence_df = dropper(binary_evidence_df)
        return log_results, fpr_df, binary_evidence_df
    except Exception as e:
        logger.error("Error handling kinase filtering: %s", e)
        raise

def handle_sample_filtering(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df: Optional[pd.DataFrame],
    manual_samples: str = ''
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Filter samples based on a comma-separated list of sample names.
    Parameters:
        log_results: DataFrame with log-transformed activity data
        fpr_df: DataFrame with FPR values
        binary_evidence_df: Optional evidence DataFrame
        manual_samples: Comma-separated list of sample names to keep 
    Returns:
        Tuple of filtered DataFrames (log_results, fpr_df, binary_evidence_df)
    """
    try:
        if manual_samples:
            samples = parse_comma_separated_list(manual_samples)
            if samples:
                log_results = log_results[samples]
                fpr_df = fpr_df[samples]
                if binary_evidence_df is not None:
                    binary_evidence_df = binary_evidence_df[samples]
        return log_results, fpr_df, binary_evidence_df
    except Exception as e:
        logger.error("Error handling sample filtering: %s", e)
        raise

def sort_by_activity(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df: Optional[pd.DataFrame],
    sort_by: str,
    ascending: bool = False,
    axis: int = 0
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Sort kinases or samples based on activity levels.
    Parameters:
        log_results: DataFrame with log-transformed activity data
        fpr_df: DataFrame with FPR values
        binary_evidence_df: Optional evidence DataFrame
        sort_by: Column (for kinases) or row (for samples) to sort by
        ascending: Sort order (default: False, highest values first)
        axis: Sort axis - 0 for kinases, 1 for samples     
    Returns:
        Tuple of sorted DataFrames (log_results, fpr_df, binary_evidence_df)
    """
    try:
        if axis == 0 and sort_by in log_results.columns:
            log_results = log_results.sort_values(by=sort_by, ascending=ascending)
            fpr_df = fpr_df.reindex(log_results.index)
            if binary_evidence_df is not None:
                binary_evidence_df = binary_evidence_df.reindex(log_results.index)
        elif axis == 1 and sort_by in log_results.index:
            sorted_cols = log_results.loc[sort_by].sort_values(ascending=ascending).index
            log_results = log_results[sorted_cols]
            fpr_df = fpr_df[sorted_cols]
            if binary_evidence_df is not None:
                binary_evidence_df = binary_evidence_df[sorted_cols]
        return log_results, fpr_df, binary_evidence_df
    except Exception as e:
        logger.error("Error sorting by activity: %s", e)
        raise
