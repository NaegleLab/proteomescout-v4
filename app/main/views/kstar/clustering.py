"""
KSTAR Clustering Module

This module provides functions for hierarchical clustering of KSTAR data
for visualization purposes. It handles clustering rows (kinases) and columns
(samples) of activity and FPR data, generating linkage matrices for dendrograms.

Functions:
    perform_clustering: Execute hierarchical clustering on rows or columns
    apply_clustering_order: Reorder dataframes based on clustering results
    cluster_and_apply: Combine clustering and result reordering
    handle_clustering_for_plot: Manage the clustering workflow for visualizations
"""

from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import linkage, leaves_list, dendrogram
import numpy as np
from typing import Tuple, Optional, Dict, Any, Union
import pandas as pd

def perform_clustering(
    data: Union[pd.DataFrame, np.ndarray],
    mode: str = 'row',
    method: str = 'ward'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform hierarchical clustering on the given data.
    
    Args:
        data: DataFrame or ndarray to cluster.
        mode: 'row' for clustering rows, 'column' for clustering columns.
        method: Linkage method to use.
        
    Returns:
        Tuple containing the linkage matrix and the leaves indices.
    """
    if isinstance(data, pd.DataFrame):
        data = data.values
    data = np.nan_to_num(data)
    if mode == 'column':
        data = data.T
    Z = linkage(data, method=method)
    leaves = leaves_list(Z)
    return Z, leaves

def apply_clustering_order(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    leaves: np.ndarray,
    mode: str = 'row',
    binary_evidence_df: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Reorder the given dataframes based on the clustering leaves order.
    
    Args:
        log_results: DataFrame with log-transformed results.
        fpr_df: DataFrame with FPR values.
        leaves: Array of indices from clustering.
        mode: 'row' to reorder rows, 'column' to reorder columns.
        binary_evidence_df: Optional DataFrame with binary evidence.
        
    Returns:
        Tuple containing the reordered dataframes.
    """
    if mode == 'row':
        log_results_reordered = log_results.iloc[leaves, :]
        fpr_df_reordered = fpr_df.iloc[leaves, :]
        if binary_evidence_df is not None:
            binary_evidence_df = binary_evidence_df.iloc[leaves, :]
    else:
        log_results_reordered = log_results.iloc[:, leaves]
        fpr_df_reordered = fpr_df.iloc[:, leaves]
        if binary_evidence_df is not None:
            binary_evidence_df = binary_evidence_df.iloc[:, leaves]
    
    return log_results_reordered, fpr_df_reordered, binary_evidence_df

def cluster_and_apply(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df: Optional[pd.DataFrame] = None,
    mode: str = 'row',
    method: str = 'ward'
) -> Tuple[np.ndarray, pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Perform hierarchical clustering and apply the resulting order to the given dataframes.
    
    Args:
        log_results: DataFrame with log-transformed results.
        fpr_df: DataFrame with FPR values.
        binary_evidence_df: Optional DataFrame with binary evidence.
        mode: 'row' for clustering rows, 'column' for clustering columns.
        method: Linkage method.
        
    Returns:
        Tuple of (linkage_matrix, reordered log_results, reordered fpr_df, 
                reordered binary_evidence_df).
    """
    Z, leaves = perform_clustering(log_results, mode=mode, method=method)
    log_results, fpr_df, binary_evidence_df = apply_clustering_order(
        log_results, fpr_df, leaves, mode, binary_evidence_df
    )
    
    return Z, log_results, fpr_df, binary_evidence_df

def handle_clustering_for_plot(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df: Optional[pd.DataFrame] = None,
    sort_settings: Optional[Dict[str, str]] = None,
    plot_params: Optional[Dict[str, Any]] = None,
    dendrogram_settings: Optional[Dict[str, bool]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Execute the complete clustering workflow for plot generation.
    
    Args:
        log_results: DataFrame with log-transformed results.
        fpr_df: DataFrame with FPR values.
        binary_evidence_df: Optional DataFrame with binary evidence.
        sort_settings: Dict with keys 'kinases_mode' and 'samples_mode'.
        plot_params: Dict of plot parameters.
        dendrogram_settings: Dict with keys for dendrogram display options.
        
    Returns:
        Tuple of (log_results, fpr_df, binary_evidence_df, row_linkage, col_linkage).
    """
    sort_settings = sort_settings or {'kinases_mode': 'none', 'samples_mode': 'none'}
    dendrogram_settings = dendrogram_settings or {
        #'show_kinases_dendrogram_outside': True,
        'show_kinases_dendrogram_inside': False,
        'show_samples_dendrogram': True
    }
    row_linkage, col_linkage = None, None

    # Perform clustering if requested
    if sort_settings.get('kinases_mode') == 'by_clustering':
        row_linkage, log_results, fpr_df, binary_evidence_df = cluster_and_apply(
            log_results, fpr_df, binary_evidence_df, mode='row'
        )
    if sort_settings.get('samples_mode') == 'by_clustering':
        col_linkage, log_results, fpr_df, binary_evidence_df = cluster_and_apply(
            log_results, fpr_df, binary_evidence_df, mode='column'
        )
    
    # Only return linkage matrices if dendrograms should be shown
    #show_kinases_dendrogram_outside = dendrogram_settings.get('show_kinases_dendrogram_outside', True)
    show_kinases_dendrogram_inside = dendrogram_settings.get('show_kinases_dendrogram_inside', False)
    show_samples_dendrogram = dendrogram_settings.get('show_samples_dendrogram', True)
    
    # Set linkage to None if dendrogram should not be shown
    row_linkage_for_display = row_linkage if show_kinases_dendrogram_inside else None
    col_linkage_for_display = col_linkage if show_samples_dendrogram else None
    
    return log_results, fpr_df, binary_evidence_df, row_linkage_for_display, col_linkage_for_display