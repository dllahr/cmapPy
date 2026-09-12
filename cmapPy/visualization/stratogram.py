
'''
Created on Sep 30, 2019

@author: Navid Dianati
@contact: navid@broadinstitute.org
'''
import logging

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger()

figure_dpi = 150


ANNOTATION_KWARGS = dict(
        zorder=100
    )

def stratogram(
    data,
    category_definition,
    category_label,
    category_order,
    metrics,
    column_display_names,
    outfile='',
    bins=51,
    colors=["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"] * 3,
    figsize=(40, 20),
    xtick_orientation="horizontal",
    ylabel_fontsize=25,
    xlabel_fontsize=25,
    xlabel_fontcolor="#555555",
    ylabel_fontcolor="#555555",
    fontfamily="Roboto"
):    
    '''
    Create a stratogram of the data. A stratogram is a grid of histograms
    of various metrics computed for a set of data points, stratified by a
    "category_definition" variable. Each column of the grid is one metric, and each row
    depicts a stratum of the data.
    @param data: Pandas DataFrame where each row is a data point and the
    metrics and other variables are in the columns.
    @param category_definition: string name of the column that defines the stratum/
    category of each data point.
    @param category_label: string name of the column that defines the stratum/
    label for each data point.
    @param category_order: string name of the integer column that defines
    the order in which each stratum should be plotted in the rows. There
    should be a one-to-one map between the category_definition and category_order
    variables. 
    @param metrics: list of column names containing numberical values
    whose histogram is plotted.
    @param column_display_names: list of display names for the metrics.
    @keyword outfile: filename to export the figure.
    @keyword bins: number of bins to use for histogram. Same for all cells.
    @keyword colors: list of colors. Each color will be plotted using one
    of these colors, in order.
    @keyword figsize
    @keyword xtick_orientation: Either "horizontal" or "vertical"
    @keyword ylabel_fontsize
    @keyword xlabel_fontsize
    @keyword xlabel_fontcolor
    @keyword ylabel_fontcolor
    @keyword fontfamily
    '''
    df = data.copy()
    column_display_names = [name + "\n" for name in column_display_names]
    
    # Make sure necessary columns are in the dataframe
    assert category_definition in df.columns
    assert category_order in df.columns

    logger.info('Validating the table')
    for metric in metrics:
        assert metric in df.columns, metric

    # Update category_definition order to "remove" non-existent categories
    dict_new_order = {x:i for i, x in  enumerate(sorted(df[category_order].unique().tolist()))}
    df[category_order] = df[category_order].apply(lambda x:dict_new_order[x])
    n_rows = df[category_order].nunique()
    
    n_cols = len(metrics)
    plt.figure(figsize=figsize, dpi=figure_dpi)
    gs = gridspec.GridSpec(n_rows, n_cols)
    gs.update(wspace=0.0, hspace=0.0)
    
    # Count the total number of test compounds
    test_categories = [c for c in df[category_definition].dropna().unique() if is_test_category(c)]
    num_test_compounds = len(df[df[category_definition].isin(test_categories)])
    
    # Group the data by the category_definition variable and for each stratum
    # Plot a row of histograms in the grid.
    grouped = df.groupby(category_definition)
    for name, group in grouped:
        row_is_test_compounds = is_test_category(name)
        name = group[category_label].unique()
        assert len(name) == 1
        name = name[0]
            
        group.name = name
        row_label = name
        n_points = len(group)
        fraction_of_tests = float(n_points) / num_test_compounds
        
        if row_is_test_compounds:
            row_sublabel = "(n={:,} - {:.0%} of test)".format(n_points, fraction_of_tests)
        else:
            row_sublabel = "(n={:,})".format(n_points)
        plot_row_of_histograms(
            group,
            gs,
            category_order,
            n_rows,
            n_cols,
            plot_columns=metrics,
            column_display_names=column_display_names,
            bins=bins,
            row_label=row_label,
            row_sublabel=row_sublabel,
            fontfamily=fontfamily,
            colors=colors,
            xtick_orientation=xtick_orientation,
            ylabel_fontsize=ylabel_fontsize,
            xlabel_fontsize=xlabel_fontsize,
            xlabel_fontcolor=xlabel_fontcolor,
            ylabel_fontcolor=ylabel_fontcolor,
            )
    
    if outfile:
        plt.savefig(outfile, bbox_inches='tight')


def is_test_category(category):
    '''Determine whether a category name identifies a "test" category (as
    opposed to e.g. a control category), based on whether the substring
    "test" (case-insensitive) appears anywhere in the category name.

    Args:
        category (string): category name

    Returns:
        bool: True if "test" (case-insensitive) is a substring of category
    '''
    return 'test' in category.lower()


def get_axis_size(ax):
    '''Get the size, in inches, of a matplotlib Axes' bounding box, based on
    the current figure's DPI scale transform.

    Args:
        ax (matplotlib.axes.Axes): axis to measure

    Returns:
        (float, float): (width, height) in inches
    '''
    bbox = ax.get_window_extent().transformed(plt.gcf().dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    return width, height


def _add_annotation_reproducibility(ax, data, metric_label, col_id, row_id, threshold=0.2, **kwargs):
    '''Overlay a dashed vertical line at threshold on ax's "reproducibility"
    histogram, annotate the threshold value on the top row, and annotate the
    count/percentage of data >= threshold.'''
    logger.info("Adding annotation for column {}".format(metric_label))
    ylim = ax.get_ylim()
    n_points = len(data)
    n_pass = len(data[data >= threshold])
    width, height = get_axis_size(ax)
    fontsize = int(height * figure_dpi * 0.08)
    ax.plot([threshold, threshold], ylim, '--', color="#aaaaaa", alpha=0.5)
    
    if row_id == 0:
        # In data coordinates
        ax.text(threshold, ylim[1] * 1.1, "{:.2f}".format(threshold),
                horizontalalignment="center",
                verticalalignment="bottom",
                fontsize=fontsize * 0.8,
                fontweight="bold",
                fontname=kwargs.get('fontfamily'),
                color="#aaaaaa",
                )
    if n_points == 0:
        return
    ax.text(0.95, 0.9, ">{:.2f} : n={:,}\n({:.0%})".format(threshold, n_pass, float(n_pass) / n_points),
            horizontalalignment="right",
            verticalalignment="top",
            fontsize=fontsize,
            color="#222222",
            fontweight="bold",
            fontname=kwargs.get('fontfamily'),
            transform=ax.transAxes,
            **ANNOTATION_KWARGS
            )
    pass


def _add_annotation_recall(ax, data, metric_label, col_id, row_id, **kwargs):
    '''Overlay a dashed vertical line at a fixed threshold of 0.05 on ax's
    "recall" histogram, annotate the threshold value on the top row, and
    annotate the count/percentage of data <= threshold.'''
    logger.info("Adding annotation for column {}".format(metric_label))
    ylim = ax.get_ylim()
    n_points = len(data)
    
    threshold = 0.05
    
    n_pass = len(data[data <= threshold])
    width, height = get_axis_size(ax)
    fontsize = int(height * figure_dpi * 0.08)
    ax.plot([threshold, threshold], ylim, '--', color="#aaaaaa", alpha=0.5)
  
    if row_id == 0:
        # In data coordinates
        ax.text(
            threshold, ylim[1] * 1.1, "{:.2f}".format(threshold),
            horizontalalignment="center",
            verticalalignment="bottom",
            fontweight="bold",
            fontsize=fontsize * 0.8,
            fontname=kwargs.get('fontfamily'),
            color="#aaaaaa",
            )
             
    if n_points == 0:
        return
    ax.text(
        0.95, 0.9, "<{:.2f} : n={:,}\n({:.0%})".format(threshold, n_pass, float(n_pass) / n_points),
        horizontalalignment="right",
        verticalalignment="top",
        fontsize=fontsize,
        color="#222222",
        fontweight="bold",
        fontname=kwargs.get('fontfamily'),
        transform=ax.transAxes,
        **ANNOTATION_KWARGS

        )
    pass


def add_annotations(ax, data, metric_label, col_id, row_id, **kwargs):
    ''' Depending on the metric being plotted,
    optionally add further annotations to the
    axis. For instance, a threshold line or
    text labels.

    If metric_label (case-insensitive, whitespace-stripped) equals
    "reproducibility", delegates to _add_annotation_reproducibility. Else, if
    "recall" (case-insensitive) is a substring of metric_label, delegates to
    _add_annotation_recall. Otherwise no annotation is added.

    Args:
        ax (matplotlib.axes.Axes): axis the histogram was plotted on
        data (pandas series): the (NaN-dropped) values plotted in the histogram
        metric_label (string): display name of the metric being plotted
        col_id (int): column index of this subplot in the grid
        row_id (int): row index of this subplot in the grid
        **kwargs: forwarded to the delegated annotation function (e.g.
            fontfamily, threshold)

    Returns:
        None
    '''
    metric_label = metric_label.strip()
#     logger.info('Adding annotations')
    logger.info(metric_label)
    if metric_label.lower() == "reproducibility":
        return _add_annotation_reproducibility(ax, data, metric_label, col_id, row_id, **kwargs)
    else:
        logger.info("'{}', '{}'".format(metric_label, 'reproducibility'))

    if 'recall' in metric_label.lower():
        return _add_annotation_recall(ax, data, metric_label, col_id, row_id, **kwargs) 


def plot_row_of_histograms(
        df, gs, category_order,
        n_rows, n_cols,
        plot_columns, column_display_names, bins,
        row_label, row_sublabel,
        fontfamily, colors,
        xtick_orientation, ylabel_fontsize, xlabel_fontsize, xlabel_fontcolor, ylabel_fontcolor):
    ''' Plot one row (stratum) of histograms into the n_rows x n_cols grid of
    subplots defined by the GridSpec gs. For each metric in plot_columns, draws
    a histogram of df[metric] (with NaNs dropped) into the corresponding
    subplot, filled with colors[col_id]. The row's position within the grid is
    taken from df[category_order] (all rows of df must share the same value).
    The top row (row_id == 0) additionally gets column header labels (via
    xlabel, placed above the axes); the leftmost column (col_id == 0)
    additionally gets row_label/row_sublabel (via ylabel and adjacent text);
    all rows except the last have their x tick labels hidden, and the last row
    keeps them, oriented per xtick_orientation. add_annotations() is called for
    every subplot to optionally overlay metric-specific annotations (e.g.
    threshold lines for "reproducibility"/"recall" metrics).

    @param df: DataFrame containing only the rows for this stratum/category.
    Must have a category_order column with a single unique value giving this
    row's position in the grid; df.name should be the stratum's identifier.
    @param gs: matplotlib.gridspec.GridSpec for the overall n_rows x n_cols grid.
    @param category_order: name of the (integer) column in df giving this
    stratum's row position in the grid.
    @param n_rows: total number of rows (strata) in the grid.
    @param n_cols: total number of columns (metrics) in the grid.
    @param plot_columns: list of column names (metrics) to plot, one per column.
    @param column_display_names: list of display names for plot_columns, used
    as the x-axis label of the top row.
    @param bins: bins to pass to plt.hist; if an int, converted to
    numpy.linspace(0, 1, bins) bin edges; otherwise used as-is (e.g. explicit
    bin edges).
    @param row_label: label text for this row, drawn via ylabel on the first column.
    @param row_sublabel: sublabel text (e.g. sample count) drawn to the left of
    the row label on the first column.
    @param fontfamily: font family used for axis tick labels.
    @param colors: list of colors, one per column/metric, used to fill the histograms.
    @param xtick_orientation: "horizontal" or "vertical"; orientation of the
    bottom row's x tick labels.
    @param ylabel_fontsize: font size for row_label/row_sublabel.
    @param xlabel_fontsize: font size for the column header labels.
    @param xlabel_fontcolor: color for the column header labels.
    @param ylabel_fontcolor: color for row_label.
    @return: None
    '''
    name = df.name
    row_id = df[category_order].unique()
    assert len(row_id) == 1
    row_id = row_id[0]
    font = fontfamily
    fontweight = 600
    
    if type(bins) == int:
        bins = np.linspace(0, 1, bins)
        
    for j, (metric, colname) in enumerate(zip(plot_columns, column_display_names)):
        col_id = j
        counter = int(row_id * n_cols + col_id)
        ax = plt.subplot(gs[counter])

        with sns.axes_style('white'):
            try:
                data = df[metric].dropna()
                plt.hist(data, bins=bins, lw=1, edgecolor="#ffffff", color=str(colors[col_id]))

            except Exception as e:
                plt.text(0.01, 0.5, 'ERROR')
                logger.error(str(e))
            
            if row_id == 0:
                plt.xlabel(colname + "  ",
                           rotation='horizontal',
                           fontweight=fontweight,
                           horizontalalignment="center",
                           fontname=font,
                           color=xlabel_fontcolor,
                           fontsize=xlabel_fontsize)
                plt.gca().xaxis.set_label_position('top') 
            if (col_id == 0):
                
                plt.text(-0.1, 0.3, row_sublabel,
                    horizontalalignment="right", fontsize=ylabel_fontsize * 0.8, color="#444444",
                        transform=ax.transAxes)
                plt.ylabel("{}  \n".format(row_label),
                           rotation='horizontal',
                           fontweight=fontweight,
                           verticalalignment="center",
                           horizontalalignment="right",
                           fontname=font,
                           color=ylabel_fontcolor,
                           fontsize=ylabel_fontsize)
                
            if row_id != n_rows - 1:
                plt.xticks([])
            else:
                if xtick_orientation == "vertical":
                    plt.xticks(rotation="vertical")
                
            plt.yticks([])
            
            annotation_kwargs = ANNOTATION_KWARGS.copy()
            annotation_kwargs.update(
                dict(fontfamily=font)
                )
            add_annotations(plt.gca(), data, colname, col_id, row_id, **annotation_kwargs)
            
                
def break_lines(s):
    '''Split a long phrase by putting the first word
    on the first line and everything else on the second
    line by inserting a newline between the two.

    @param s: string to split, with words separated by single spaces.
    @return: s unchanged if it has only one word; otherwise a string with the
    first word, a newline, then the remaining words joined by spaces.
    '''
    x = s.split(" ")
    if len(x) == 1:
        return s
    return "{}\n{}".format(x[0], " ".join(x[1:]))
       
