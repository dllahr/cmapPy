'''
diff_gctoo.py

Converts a matrix of values (e.g. gene expression, viability, etc.) into a
matrix of differential values. Values can be made differential relative to all
samples in the dataset ("plate-control") or relative to just negative control
samples ("vehicle-control"). The method of computing the differential can be
either a robust z-score ("robust_z") or simply median normalization
("median_norm").

'''
import cmapPy.math.robust_zscore as robust_zscore
import cmapPy.pandasGEXpress.GCToo as GCToo

possible_diff_methods = ["robust_z", "median_norm"]


def diff_gctoo(gctoo, plate_control=True, group_field='pert_type', group_val='ctl_vehicle',
               diff_method="robust_z", upper_diff_thresh=10, lower_diff_thresh=-10):
    ''' Converts a matrix of values (e.g. gene expression, viability, etc.)
    into a matrix of differential values.

    If plate_control is True, the robust z-score ("robust_z") or median
    ("median_norm") used to compute the differential is calculated from
    gctoo.data_df as a whole (i.e. relative to all samples in the dataset -
    "plate control"). If plate_control is False, the negative control (
    "vehicle control") samples are first identified as those columns where
    gctoo.col_metadata_df[group_field] == group_val, and the robust z-score
    ("robust_z") or median ("median_norm") is computed relative to just
    those samples. Resulting differential data is clipped to lie within
    [lower_diff_thresh, upper_diff_thresh].

    Args:
    gctoo (GCToo object): data to make differential (uses gctoo.data_df,
        gctoo.row_metadata_df, and, if plate_control is False, gctoo.col_metadata_df)
    plate_control (bool): True means calculate diff_gctoo using plate control
        (relative to all samples). False means vehicle control (relative to
        the negative control samples identified via group_field/group_val).
    group_field (string): Metadata field (column of gctoo.col_metadata_df) in
        which to find group_val; only used when plate_control is False
    group_val (string): Value in group_field that indicates a negative
        control ("vehicle control") sample; only used when plate_control is False
    diff_method (string): Method of computing differential data; currently only
        support either "robust_z" or "median_norm"
    upper_diff_thresh (float): Maximum value for diff data (values above this are clipped)
    lower_diff_thresh (float): Minimum value for diff data (values below this are clipped)

    Returns:
    out_gctoo (GCToo object): GCToo with differential data values (same
        row_metadata_df and col_metadata_df as the input gctoo)

    Raises:
        AssertionError: if diff_method is not one of possible_diff_methods,
            if plate_control is False and group_field is not a column of
            gctoo.col_metadata_df, or if no samples match group_val in group_field
    '''
    assert diff_method in possible_diff_methods, (
        "possible_diff_methods: {}, diff_method: {}".format(
            possible_diff_methods, diff_method))

    # Compute median and MAD using all samples in the dataset
    if plate_control:

        # Compute differential data
        if diff_method == "robust_z":
            diff_data = robust_zscore.robust_zscore(gctoo.data_df)

        elif diff_method == "median_norm":
            medians = gctoo.data_df.median(axis=1)
            diff_data = gctoo.data_df.subtract(medians, axis='index')

    # Compute median and MAD from negative controls, rather than all samples
    else:

        assert group_field in gctoo.col_metadata_df.columns.values, (
            "group_field {} not present in column metadata. " +
            "gctoo.col_metadata_df.columns.values: {}").format(
            group_field, gctoo.col_metadata_df.columns.values)

        assert sum(gctoo.col_metadata_df[group_field] == group_val) > 0, (
            "group_val {} not present in the {} column.").format(
            group_val, group_field)

        # Find negative control samples
        neg_ctl_samples = gctoo.col_metadata_df.index[gctoo.col_metadata_df[group_field] == group_val]
        neg_ctl_df = gctoo.data_df[neg_ctl_samples]

        # Compute differential data
        if diff_method == "robust_z":
            diff_data = robust_zscore.robust_zscore(gctoo.data_df, neg_ctl_df)

        elif diff_method == "median_norm":
            medians = neg_ctl_df.median(axis=1)
            diff_data = gctoo.data_df.subtract(medians, axis='index')

    # Threshold differential data before returning
    diff_data = diff_data.clip(lower=lower_diff_thresh, upper=upper_diff_thresh)

    # Construct output GCToo object
    out_gctoo = GCToo.GCToo(data_df=diff_data,
                            row_metadata_df=gctoo.row_metadata_df,
                            col_metadata_df=gctoo.col_metadata_df)

    return out_gctoo

