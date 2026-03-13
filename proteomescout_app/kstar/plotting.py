import matplotlib
matplotlib.use('Agg')  # Render in-memory
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from io import BytesIO
import base64
from typing import Any, Union
from scipy.cluster.hierarchy import linkage, dendrogram
from .dotplot import DotPlot

"""
KSTAR Visualization Module

This module provides functions for creating dot plots and hierarchical clustering 
visualizations from KSTAR analysis data. It supports both simple dot plots and 
integrated plots with optional dendrograms for hierarchical clustering.

Functions:
    draw_dendrogram: Renders dendrograms with customizable styling
    reorder_dataframe: Reorders dataframe rows/columns based on dendrogram leaves
    figure_to_base64: Converts matplotlib figures to base64-encoded images
    create_dot_plot: Creates a simple dot plot visualization
    create_integrated_plot: Creates an advanced plot with optional dendrograms
"""

def draw_dendrogram(
    ax,
    linkage_matrix: np.ndarray,
    orientation: str = 'top',
    color_threshold: float = -np.inf,
    no_labels: bool = True,
    show_leaf_counts: bool = False,
    link_color_func=None,
    dendrogram_color=None
) -> dict:
    """
    Draw a dendrogram on the given matplotlib axis with customized styling.
    
    Parameters:
        ax: Matplotlib axis to draw on
        linkage_matrix: Hierarchical clustering linkage matrix
        orientation: Position of dendrogram ('top', 'bottom', 'left', 'right')
        dendrogram_color: Optional color override for all dendrogram lines
        
    Returns:
        Dictionary containing dendrogram data including leaf ordering
    """

    # If a dendrogram color is specified, create a function that returns that color
    if dendrogram_color:
        original_link_color_func = link_color_func
        link_color_func = lambda k: dendrogram_color

    
    den = dendrogram(
        linkage_matrix,
        ax=ax,
        orientation=orientation,
        color_threshold=color_threshold,
        no_labels=no_labels,
        show_leaf_counts=show_leaf_counts,
        link_color_func=link_color_func
    )
    # Remove all ticks initially
    ax.set_xticks([])
    ax.set_yticks([])

    if orientation in ['left', 'right']:
        # keep left/top/bottom spines; drop right spine
        for side in ['left', 'top', 'bottom']:
            ax.spines[side].set_visible(True)
        ax.spines['right'].set_visible(False)
    else:
        # no frame for top/bottom orientations
        for spine in ax.spines.values():
            spine.set_visible(False)

    return den


def reorder_dataframe(
    df: pd.DataFrame,
    leaves: list,
    axis: int = 0
) -> pd.DataFrame:
    """
    Reorder dataframe rows or columns based on dendrogram leaf ordering.
    
    Parameters:
        df: Pandas DataFrame to reorder
        leaves: List of indices from dendrogram leaves
        axis: 0 for rows, 1 for columns
        
    Returns:
        Reordered DataFrame
    """
    return df.iloc[leaves] if axis == 0 else df.iloc[:, leaves]


def figure_to_base64(
    fig: plt.Figure,
    dpi: int = 150,
    bbox_inches: str = 'tight',
    pad_inches: float = 0.01
) -> str:
    """
    Convert matplotlib figure to base64 encoded string for web display.
    
    Parameters:
        fig: Matplotlib Figure
        dpi: Resolution for the output image
        
    Returns:
        Base64-encoded PNG image as string
    """
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches=bbox_inches, pad_inches=pad_inches)
    buf.seek(0)
    img = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return img


def create_dot_plot(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df=None,  # Kept for backward compatibility
    download: bool = False,
    show_evidence: bool = False,  # Kept for backward compatibility
    add_additional_context: bool = False,  # Kept for backward compatibility
    **kwargs: Any
) -> Union[str, plt.Figure]:
    """
    Create a simple KSTAR dot plot visualization.
    
    Parameters:
        log_results: DataFrame with kinase activity data
        fpr_df: DataFrame with FPR values
        download: Return Figure object instead of base64 string if True
        kwargs: Additional parameters including:
            - fig_width, fig_height: Figure dimensions
            - background_color: Plot background color
            - activity_color, noactivity_color: Dot colors for activity states
            - dot_scaling: Size of dots relative to significance
            - fontsize: Text size for axis labels
            
    Returns:
        Base64-encoded PNG (if download=False) or matplotlib Figure (if download=True)
    """
    fig_w = float(kwargs.get('fig_width', 4.0))
    fig_h = float(kwargs.get('fig_height', 10.0))
    bgc = kwargs.get('background_color', '#ffffff')

    dp = DotPlot(
        values=log_results,
        fpr=fpr_df,
        binary_sig=bool(kwargs.get('binary_sig', True)),
        colormap={0: kwargs.get('noactivity_color', '#377eb8'),
                  1: kwargs.get('activity_color', '#e41a1c')},
        dotsize=kwargs.get('dot_scaling', 5),
        facecolor=bgc,
        figsize=(fig_w, fig_h),
        x_label_dict=kwargs.get('custom_xlabels'),
        kinase_dict=kwargs.get('kinase_dict'),
        legend_distance=kwargs.get('legend_distance', 1.0)
    )
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), constrained_layout=False)
    fig.patch.set_facecolor(bgc)
    dp.dotplot(
        ax=ax,
        orientation='left',
        size_legend=bool(kwargs.get('show_size_legend', True)),
        color_legend=bool(kwargs.get('show_color_legend', True))
    )
    ax.tick_params(axis='y', labelsize=kwargs.get('fontsize', 10))
    ax.tick_params(axis='x', labelsize=kwargs.get('fontsize', 10), rotation=90)
    ax.set_facecolor(bgc)
    return fig if download else figure_to_base64(fig, dpi=kwargs.get('dpi', 150))


def create_integrated_plot(
    log_results: pd.DataFrame,
    fpr_df: pd.DataFrame,
    binary_evidence_df=None,  # Kept for backward compatibility
    row_linkage=None,
    col_linkage=None,
    download: bool = False,
    show_evidence: bool = False,  # Kept for backward compatibility
    add_additional_context: bool = False,  # Kept for backward compatibility
    **kwargs: Any
) -> Union[str, plt.Figure]:
    """
    Create an integrated KSTAR visualization with optional dendrograms.
    
    Parameters:
        log_results: DataFrame with kinase activity data
        fpr_df: DataFrame with FPR values
        row_linkage: Pre-computed row/kinase linkage matrix (optional)
        col_linkage: Pre-computed column/sample linkage matrix (optional)
        download: Return Figure object instead of base64 string if True
        kwargs: Additional parameters including:
            - show_samples_dendrogram: Display sample clustering dendrogram
            - show_kinases_dendrogram_inside: Display kinase clustering dendrogram
            - dendrogram_method: Clustering method (default: 'ward')
            - dendrogram_metric: Distance metric (default: 'euclidean')
            - dendrogram colors: Colors for dendrograms
            - All parameters accepted by create_dot_plot
            
    Returns:
        Base64-encoded PNG (if download=False) or matplotlib Figure (if download=True)
    """
    """
    Mirrors Streamlit's kstar_plot GridSpec:
      - Optional sample dendrogram on top row
      - Main row: [inside kinase-dendrogram] [dotplot]
    """
    sort_samples = bool(kwargs.get('show_samples_dendrogram', False))
    sort_inside = bool(kwargs.get('show_kinases_dendrogram_inside', False))
    # Removed include_evidence line

    method = kwargs.get('dendrogram_method', 'ward')
    metric = kwargs.get('dendrogram_metric', 'euclidean')
    
    kinases_dendrogram_color = kwargs.get('kinases_dendrogram_color', '#000000')
    samples_dendrogram_color = kwargs.get('samples_dendrogram_color', '#000000')

    dp = DotPlot(
        values=log_results.copy(),
        fpr=fpr_df.copy(),
        binary_sig=bool(kwargs.get('binary_sig', True)),
        colormap={0: kwargs.get('noactivity_color', '#377eb8'),
                  1: kwargs.get('activity_color', '#e41a1c')},
        dotsize=kwargs.get('dot_scaling', 5),
        facecolor=kwargs.get('background_color', '#ffffff'),
        figsize=(float(kwargs.get('fig_width', 4.0)),
                 float(kwargs.get('fig_height', 10.0))),
        x_label_dict=kwargs.get('custom_xlabels'),
        kinase_dict=kwargs.get('kinase_dict'),
        legend_distance=kwargs.get('legend_distance', 1.0),
    )

    # Determine grid layout - simplified without evidence row
    nrows = 1 + int(sort_samples)  # Only sample dendrogram + main plot
    if sort_samples:
        height_ratios = [0.05, 1]  # Sample dendrogram, Main plot
    else:
        height_ratios = [1]  # Only main plot

    ncols = 1 + (1 if sort_inside else 0)
    width_ratios = ([0.1] if sort_inside else []) + [1]

    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=dp.figsize,
        height_ratios=height_ratios,
        width_ratios=width_ratios,
        sharex='col', sharey='row',
        constrained_layout=False
    )
    fig.patch.set_facecolor(dp.facecolor)
    fig.subplots_adjust(wspace=0, hspace=0.01)

    axes = np.array(axes, copy=False)
    if axes.ndim == 0:
        axes = axes.reshape(1, 1)
    elif axes.ndim == 1:
        axes = axes.reshape((nrows, ncols))
    data_column = 1 if sort_inside else 0

    # --- Draw Components ---

    # Sample dendrogram (top)
    if sort_samples:
        ax_s = axes[0, -1]
        # Use provided linkage if available (should always be available if clustering was selected)
        link = col_linkage if col_linkage is not None else linkage(dp.values.values.T, method=method, metric=metric)
        # Draw the dendrogram
        den = draw_dendrogram(ax_s, link, orientation='top', dendrogram_color=samples_dendrogram_color)
        ax_s.set_yticks([])
        if sort_inside:
            axes[0, 0].axis('off')

    # Inside kinase dendrogram (left)
    if sort_inside:
        r = 1 if sort_samples else 0
        ax_d = axes[r, 0]
        # Use provided linkage if available, otherwise calculate it
        link = row_linkage if row_linkage is not None else linkage(dp.values.values, method=method, metric=metric)
        den = draw_dendrogram(ax_d, link, orientation='left', dendrogram_color=kinases_dendrogram_color)

        ax_d.tick_params(axis='both', which='both', length=0)
        ax_d.set_xticks([])

    # Main dotplot
    data_col = 1 if sort_inside else 0
    r = 1 if sort_samples else 0
    ax_main = axes[r, data_col]
    dp.dotplot(
        ax_main,
        orientation='left',
        size_legend=bool(kwargs.get('show_size_legend', True)),
        color_legend=bool(kwargs.get('show_color_legend', True))
    )
    ax_main.tick_params(axis='y', labelsize=kwargs.get('fontsize', 10))
    ax_main.tick_params(axis='x', labelsize=kwargs.get('fontsize', 10), rotation=90)
    ax_main.set_facecolor(dp.facecolor)

    return fig if download else figure_to_base64(fig, dpi=kwargs.get('dpi', 150))
