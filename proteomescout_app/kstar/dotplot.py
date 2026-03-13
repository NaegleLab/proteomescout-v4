import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.cm as cm

"""
KSTAR DotPlot Visualization Module

This module provides a class for creating highly customizable dot plots for KSTAR 
visualization. Dots represent kinase activities, with size corresponding to activity
magnitude and color indicating statistical significance.
Classes:
    OrientationError: Custom exception for invalid plot orientations
    DotPlot: Main class for creating and customizing dot plot visualizations
"""

class OrientationError(Exception):
    """
    Exception raised when an invalid orientation is provided to the dotplot method.
    Valid orientations are 'left' and 'right'.
    """
    def __init__(self, message = "Orientation Invalid. Valid Orientations are: ", valid_orientations = ['left', 'right']):
        self.message = message + ', '.join(valid_orientations)
    def __str__(self):
        return self.message

class DotPlot:
    """
    Class for creating dot plot visualizations of kinase activity data.
    The visualization represents kinase activity as dots where:
    - Size corresponds to the magnitude of activity
    - Color indicates significance (binary or continuous based on FPR values)
    Parameters:
        values: DataFrame with kinase activity values
        fpr: DataFrame with false positive rate (FPR) values
        alpha: Significance threshold (default: 0.05)
        inclusive_alpha: Whether threshold is inclusive (default: True)
        binary_sig: Use binary coloring for significance (default: True)
        dotsize: Base size multiplier for dots (default: 5)
        colormap: Dictionary mapping significance states to colors
        facecolor: Background color for the plot
        legend_title: Title for the legend
        x_label_dict: Dictionary or list for custom column labels
        kinase_dict: Dictionary for custom row/kinase labels
    Methods:
        set_column_labels: Configure custom labels for columns (samples)
        set_index_labels: Configure custom labels for rows (kinases)
        dotplot: Generate the dot plot visualization on a given axis
    """

    def __init__(self, values, fpr, alpha = 0.05, inclusive_alpha = True,
                 binary_sig = True, dotsize = 5, 
                 colormap={0: '#6b838f', 1: '#FF3300'}, facecolor = 'white',
                 labelmap = None,
                 legend_title = 'p-value', size_number = 5, size_color = 'gray', 
                 color_title = 'Significant', markersize = 10, 
                 legend_distance = 1.0, figsize = (20,4), title = None,
                 xlabel = True, ylabel = True, x_label_dict = None, kinase_dict = None):

        self.values = values.copy()
        self.fpr = fpr.copy()
        # ensure fpr has same index and columns as values
        self.fpr = self.fpr.loc[self.values.index, self.values.columns]
        self.alpha = alpha
        if inclusive_alpha:
            self.significance = (self.fpr <= alpha).astype(int)
        else:
            self.significance = (self.fpr < alpha).astype(int)

        # Assign either fpr or significance as colors
        self.binary_sig = binary_sig
        if binary_sig:
            self.colors = self.significance
            if labelmap is None:
                if inclusive_alpha:
                    self.labelmap = {0: f'FPR > {alpha:0.2f}', 1: f'FPR <= {alpha:0.2f}'}
                else:
                    self.labelmap = {0: f'FPR >= {alpha:0.2f}', 1: f'FPR < {alpha:0.2f}'}
            else:
                self.labelmap = labelmap
        else:
            self.colors = self.fpr
            self.labelmap = labelmap or {}

        self.dotsize = dotsize
        self.colormap = colormap
        self.facecolor = facecolor
        self.legend_title = legend_title
        self.size_number = size_number
        self.size_color = size_color
        self.markersize = markersize
        self.color_title = color_title
        self.legend_distance = legend_distance
        self.figsize = figsize
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.x_label_dict = x_label_dict

        # multipliers for spacing
        self.multiplier = 10
        self.offset = self.multiplier/2

        # initialize labels
        self.set_column_labels(values, x_label_dict)
        self.set_index_labels(values, kinase_dict)

    def set_column_labels(self, values, x_label_dict):
        """
        Configure custom labels for columns (samples).
        Parameters:
            values: DataFrame whose columns need labels
            x_label_dict: Dictionary mapping column names to display labels or
                          list of labels in column order
        """
        self.column_labels = list(self.values.columns)

        if x_label_dict is None:
            # build a default x_label_dict stripping 'data:' prefix
            self.x_label_dict = {}
            for col in self.column_labels:
                clean = col.replace('data:', '')
                self.x_label_dict[col] = clean
            self.column_labels = [self.x_label_dict[col] for col in self.column_labels]
        elif isinstance(x_label_dict, dict):
            # Handle dictionary case
            if set(x_label_dict.keys()) != set(self.column_labels):
                raise ValueError("The x_label_dict must have the same elements as the value columns")
            self.column_labels = [x_label_dict[col] for col in self.column_labels]
            self.x_label_dict = x_label_dict
        elif isinstance(x_label_dict, list):
            # Handle list case
            if len(x_label_dict) != len(self.column_labels):
                raise ValueError("The x_label_list must have same length as value columns")
            self.x_label_dict = {col: label for col, label in zip(self.values.columns, x_label_dict)}
            self.column_labels = x_label_dict
        else:
            raise TypeError("x_label_dict must be either None, a dictionary, or a list")

    def set_index_labels(self, values, kinase_dict):
        """
        Configure custom labels for rows (kinases).
        Parameters:
            values: DataFrame whose indices need labels
            kinase_dict: Dictionary mapping kinase IDs to display names
        """
        self.index_labels = list(self.values.index)
        if kinase_dict is None:
            self.kinase_dict = kinase_dict
        elif isinstance(kinase_dict, dict):
            if not set(self.index_labels).issubset(set(kinase_dict.keys())):
                raise ValueError("The kinase_dict must contain at least all the kinases found in values")
            self.index_labels = [kinase_dict[idx] for idx in self.index_labels]
            self.kinase_dict = kinase_dict
        else:
            raise TypeError("If wanting to do a custom naming system, a dictionary must be provided in the 'kinase_dict' parameter")

    def dotplot(self, ax = None, orientation = 'left', size_legend = True, color_legend = True, max_size = None):
        """
        Generate the dot plot visualization on a given axis.
        Parameters:
            ax: Matplotlib axis to draw on (creates one if None)
            orientation: Legend placement ('left' or 'right')
            size_legend: Whether to display the size legend
            color_legend: Whether to display the color/significance legend
            max_size: Maximum size value for custom size legend
        Returns:
            Matplotlib axis with the generated plot
        """
        valid_orientations = ['left', 'right']
        if orientation not in valid_orientations:
            raise OrientationError(valid_orientations = valid_orientations)

        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_facecolor(self.facecolor)

        values = self.values
        num_sites = values.values.flatten()
        # size mapping
        dot_size = self.dotsize
        sizes = num_sites * dot_size

        # color mapping
        if self.binary_sig:
            # Binary case: keep original colors
            flat_values = self.colors.values.flatten()
            colors = np.array([self.colormap[int(v)] for v in flat_values])
        else:
            # Continuous case: create a colormap and transform FPR values with -log10
            cmap = LinearSegmentedColormap.from_list("sig_cmap", [self.colormap[0], self.colormap[1]])
            norm = Normalize(vmin=0, vmax=2, clip=True)
            
            # Get FPR values and transform them
            fpr_values = self.colors.values.flatten()
            fpr_values = np.where(fpr_values == 0, 0.01, fpr_values)  # Replace 0 with 0.01 to avoid log errors
            log_values = -np.log10(fpr_values)
            
            # Apply the colormap
            colors = cmap(norm(log_values))

        # determine positions
        n_rows, n_cols = values.shape
        x = np.tile(np.arange(n_cols) * self.multiplier + self.offset, n_rows)
        y = np.repeat((np.arange(n_rows) * self.multiplier + self.offset)[::-1], n_cols)

        ax.scatter(x, y, s=sizes, c=colors)

        # --- LEGENDS ---
        # Significance/color legend
        if color_legend:
            if self.binary_sig:
                # Binary case - use self.labelmap for consistent labels
                color_legend_handles = []
                for color_key in self.colormap.keys():
                    color_legend_handles.append(
                        Line2D([0], [0], marker='o', color='w', label=self.labelmap[color_key],
                               markerfacecolor=self.colormap[color_key], markersize=self.markersize)
                    )
                sig_legend = ax.legend(handles=color_legend_handles, 
                                       loc=f'upper {orientation}', 
                                       bbox_to_anchor=(self.legend_distance, 1),
                                       title=self.color_title)
            else:
                # Continuous case - use explicit FPR values with -log10 transform
                legend_vals = [1, 0.5, 0.05, 0.01]
                cmap = LinearSegmentedColormap.from_list('custom', [self.colormap[1], self.colormap[0]])
                norm = Normalize(vmin=0, vmax=2, clip=True)
                mapper = cm.ScalarMappable(norm=norm, cmap=cmap)
                color_legend_handles = []
                for val in legend_vals:
                    color_legend_handles.append(
                        Line2D([0], [0], marker='o', color='w', label=str(val),
                               markerfacecolor=mapper.to_rgba(-np.log10(val)), 
                               markersize=self.markersize)
                    )
                sig_legend = ax.legend(handles=color_legend_handles, 
                                      loc=f'upper {orientation}', 
                                      bbox_to_anchor=(self.legend_distance, 1),
                                      title='FPR')
            sig_legend.set_clip_on(False)
            ax.add_artist(sig_legend)

        # Add Size Legend
        if size_legend:
            if max_size is not None:
                # Your existing code for custom size legend
                s_label = np.arange(max_size/self.size_number, max_size+1, max_size/self.size_number).astype(int)
                dsize = [s*self.dotsize for s in s_label]
            else:
                # Use default sizes when max_size is not provided
                s_label = [8, 16, 24, 32]  # Default size values
                dsize = [s*self.dotsize for s in s_label]
            
            # Create legend handles (same for both cases)
            size_legend_handles = []
            for element, s in zip(s_label, dsize):
                size_legend_handles.append(
                    Line2D([0], [0], marker='o', color='w', 
                           markersize=s**0.5, 
                           markerfacecolor=self.size_color, 
                           label=element)
                )
            size_legend = ax.legend(handles=size_legend_handles, 
                                   loc=f'lower {orientation}', 
                                   title='Size', 
                                   bbox_to_anchor=(self.legend_distance, 0))
            size_legend.set_clip_on(False)

        ax.set_xticks(np.arange(n_cols) * self.multiplier + self.offset)
        ax.set_xticklabels(self.column_labels, rotation=90)
        ax.set_yticks(np.arange(n_rows) * self.multiplier + self.offset)
        ax.set_yticklabels(self.index_labels[::-1])
        ax.margins(x=self.offset/(self.multiplier*n_cols), y=self.offset/(self.multiplier*n_rows))
        if not self.xlabel:
            ax.axes.xaxis.set_visible(False)
        if not self.ylabel:
            ax.axes.yaxis.set_visible(False)
        return ax
