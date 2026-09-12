import logging
import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger
import os
import numpy as np
import pandas as pd
import h5py
import cmapPy.pandasGEXpress.GCToo as GCToo

__author__ = "Oana Enache"
__email__ = "oana@broadinstitute.org"

# instantiate logger
logger = logging.getLogger(setup_logger.LOGGER_NAME)

version_node = "version"
rid_node = "/0/META/ROW/id"
cid_node = "/0/META/COL/id"
data_node = "/0/DATA/0/matrix"
row_meta_group_node = "/0/META/ROW"
col_meta_group_node = "/0/META/COL"


def parse(gctx_file_path, convert_neg_666=True, rid=None, cid=None,
          ridx=None, cidx=None, row_meta_only=False, col_meta_only=False, make_multiindex=False,
          sort_col_meta = True, sort_row_meta = True):
    """
    Primary method of script. Reads in path to a gctx file and parses into GCToo object.

    Input:
        Mandatory:
        - gctx_file_path (str): full path to gctx file you want to parse.

        Optional:
        - convert_neg_666 (bool): whether to convert -666 values to numpy.nan or not
            (see Note below for more details on this). Default = True.
        - rid (list of strings): list of row ids to specifically keep from gctx. Default=None.
        - cid (list of strings): list of col ids to specifically keep from gctx. Default=None.
        - ridx (list of integers): only read the rows corresponding to this
            list of integer ids. Default=None.
        - cidx (list of integers): only read the columns corresponding to this
            list of integer ids. Default=None.
        - row_meta_only (bool): Whether to load data + metadata (if False), or just row metadata (if True)
            as pandas DataFrame
        - col_meta_only (bool): Whether to load data + metadata (if False), or just col metadata (if True)
            as pandas DataFrame
        - make_multiindex (bool): whether to create a multi-index df combining
            the 3 component dfs
        - sort_col_meta (bool) : whether to sort the column metadata by indexes. Default = True
        - sort_row_meta (bool) : whether to sort the row metadata by indexes. Default = True
    Output:
        - myGCToo (GCToo): A GCToo instance containing content of parsed gctx file. Note: if meta_only = True,
            this will be a GCToo instance where the data_df is empty, i.e. data_df = pd.DataFrame(index=rids,
            columns = cids)

    Note: why does convert_neg_666 exist?
        - In CMap--for somewhat obscure historical reasons--we use "-666" as our null value
        for metadata. However (so that users can take full advantage of pandas' methods,
        including those for filtering nan's etc) we provide the option of converting these
        into numpy.NaN values, the pandas default.
    """
    full_path = os.path.expanduser(gctx_file_path)

    # Verify that the  path exists
    if not os.path.exists(full_path):
        err_msg = "The given path to the gctx file cannot be found. full_path: {}"
        logger.error(err_msg.format(full_path))
        raise Exception(err_msg.format(full_path))
    logger.info("Reading GCTX: {}".format(full_path))

    # open file
    gctx_file = h5py.File(full_path, "r")

    if row_meta_only:
        # read in row metadata
        row_dset = gctx_file[row_meta_group_node]
        row_meta = parse_metadata_df("row", row_dset, convert_neg_666)

        # validate optional input ids & get indexes to subset by
        (sorted_ridx, sorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, None, 
                                                                sort_row_meta = True, sort_col_meta = True)

        gctx_file.close()

        # subset if specified, then return
        row_meta = row_meta.iloc[sorted_ridx]

        if not sort_row_meta:
            (unsorted_ridx, _) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, None,
                                                      sort_row_meta, sort_row_meta)
            row_meta = row_meta.iloc[unsorted_ridx]

        return row_meta
    elif col_meta_only:
        # read in col metadata
        col_dset = gctx_file[col_meta_group_node]
        col_meta = parse_metadata_df("col", col_dset, convert_neg_666)

        # validate optional input ids & get indexes to subset by
        (sorted_ridx, sorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, None, 
                                                            col_meta, sort_row_meta = True, sort_col_meta = True)

        gctx_file.close()

        # subset if specified, then return
        col_meta = col_meta.iloc[sorted_cidx]

        if not sort_col_meta:
            (_, unsorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, None, col_meta, 
                                                        sort_row_meta, sort_col_meta)
            col_meta = col_meta.iloc[unsorted_cidx, :]

        return col_meta
    else:
        # read in row metadata
        row_dset = gctx_file[row_meta_group_node]
        row_meta = parse_metadata_df("row", row_dset, convert_neg_666)

        # read in col metadata
        col_dset = gctx_file[col_meta_group_node]
        col_meta = parse_metadata_df("col", col_dset, convert_neg_666)

        # validate optional input ids & get indexes to subset by
        (sorted_ridx, sorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, col_meta, 
                                                                sort_row_meta = True, sort_col_meta = True)

        data_dset = gctx_file[data_node]
        data_df = parse_data_df(data_dset, sorted_ridx, sorted_cidx, row_meta, col_meta)

        # (if subsetting) subset metadata
        row_meta = row_meta.iloc[sorted_ridx]
        col_meta = col_meta.iloc[sorted_cidx]

        if not sort_col_meta:
            ## in the subsetted and re-indexed dataframe get where new indexes lie
            (_, unsorted_cidx) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, col_meta, 
                                                        sort_row_meta, sort_col_meta)
            
            data_df = data_df.iloc[:,unsorted_cidx]
            col_meta = col_meta.iloc[unsorted_cidx,:]
        
        if not sort_row_meta:
            (unsorted_ridx, _) = check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta, col_meta,
                                                      sort_row_meta, sort_row_meta)
            data_df = data_df.iloc[unsorted_ridx,:]
            row_meta = row_meta.iloc[unsorted_ridx,:]

        # get version
        my_version = gctx_file.attrs[version_node]
        if type(my_version) == np.ndarray:
            my_version = my_version[0]

        gctx_file.close()

        # make GCToo instance
        my_gctoo = GCToo.GCToo(data_df=data_df, row_metadata_df=row_meta, col_metadata_df=col_meta,
                               src=full_path, version=my_version, make_multiindex=make_multiindex)
        return my_gctoo


def check_and_order_id_inputs(rid, ridx, cid, cidx, row_meta_df, col_meta_df, sort_row_meta, sort_col_meta):
    """
    Makes sure that (if entered) id inputs entered are of one type (string id or index),
    validates them against the parsed metadata, and converts them into ordered
    positional indexes to use for subsetting.

    Input:
        - rid (list or None): if not None, a list of rids
        - ridx (list or None): if not None, a list of indexes
        - cid (list or None): if not None, a list of cids
        - cidx (list or None): if not None, a list of indexes
        - row_meta_df (pandas DataFrame or None): parsed row metadata to validate/
            subset against (its index is the full set of rids); None if row
            metadata isn't being used (e.g. col_meta_only case).
        - col_meta_df (pandas DataFrame or None): parsed col metadata to validate/
            subset against (its index is the full set of cids); None if col
            metadata isn't being used (e.g. row_meta_only case).
        - sort_row_meta (bool): boolean indicating whether to return sorted row indexes
        - sort_col_meta (bool): boolean indicating whether to return sorted column indexes
    Output:
        - a tuple (ordered_ridx, ordered_cidx) of the row and column positional
            indexes to subset by (None for whichever dimension has no
            corresponding meta_df).
    """
    (row_type, row_ids) = check_id_idx_exclusivity(rid, ridx)
    (col_type, col_ids) = check_id_idx_exclusivity(cid, cidx)


    row_ids = check_and_convert_ids(row_type, row_ids, row_meta_df, sort_row_meta)
    ordered_ridx = get_ordered_idx(row_type, row_ids, row_meta_df, sort_row_meta)

    col_ids = check_and_convert_ids(col_type, col_ids, col_meta_df, sort_col_meta)
    ordered_cidx = get_ordered_idx(col_type, col_ids, col_meta_df, sort_col_meta)
    return (ordered_ridx, ordered_cidx)


def check_id_idx_exclusivity(id, idx):
    """
    Makes sure user didn't provide both ids and idx values to subset by.

    Input:
        - id (list or None): if not None, a list of string id names
        - idx (list or None): if not None, a list of integer id indexes

    Output:
        - a tuple: first element is subset type, second is subset content
    """
    if (id is not None and idx is not None):
        msg = ("'id' and 'idx' fields can't both not be None," +
               " please specify subset in only one of these fields")
        logger.error(msg)
        raise Exception("parse_gctx.check_id_idx_exclusivity: " + msg)
    elif id is not None:
        return ("id", id)
    elif idx is not None:
        return ("idx", idx)
    else:
        return (None, [])


def check_and_convert_ids(id_type, id_list, meta_df, sort_id):
    """
    If subsetting by id ("rid"/"cid"), converts id_list's entries to the same
    dtype as meta_df's index and checks that they're all present in it. If
    subsetting by positional index ("ridx"/"cidx") and sort_id is True,
    checks that all indexes are within range. Does nothing if meta_df is
    None (i.e. that dimension's metadata isn't being parsed).

    Input:
        - id_type (str): either "id", "idx", or None (see check_id_idx_exclusivity)
        - id_list (list): list of ids or indexes to check/convert (empty if id_type is None)
        - meta_df (pandas DataFrame or None): metadata dataframe to validate against
        - sort_id (bool): whether idx-based validation should check indexes are in range

    Output:
        - id_list (list or None): the (possibly type-converted) id_list, or None
            if meta_df was None.

    Raises:
        Exception if any id is not present in meta_df.index, if any idx is out
        of range, or if id_list's dtype can't be converted to meta_df.index's dtype.
    """
    if meta_df is not None:
        if id_type == "id":
            id_list = convert_ids_to_meta_type(id_list, meta_df)
            check_id_validity(id_list, meta_df)
        else:
            check_idx_validity(id_list, meta_df, sort_id)
        return id_list
    else:
        return None


def check_id_validity(id_list, meta_df):
    """
    Checks that every entry of id_list is present in meta_df's index.

    Input:
        - id_list (list): list of ids to check
        - meta_df (pandas DataFrame): metadata dataframe whose index holds
            the full set of valid ids

    Output:
        None

    Raises:
        Exception listing the mismatched ids, if any of id_list's entries
        are not present in meta_df.index.
    """
    id_set = set(id_list)
    meta_set = set(meta_df.index)
    mismatch_ids = id_set - meta_set
    if len(mismatch_ids) > 0:
        msg = "some of the ids being used to subset the data are not present in the metadata for the file being parsed - mismatch_ids:  {}".format(
            mismatch_ids)
        logger.error(msg)
        raise Exception("parse_gctx check_id_validity " + msg)


def check_idx_validity(id_list, meta_df, sort_id):
    """
    If sort_id is True, checks that every entry of id_list (positional
    indexes) is within the valid range [0, N) where N is the number of
    rows in meta_df. (If sort_id is False, no check is performed, since in
    that case id_list is being used only to compute a re-ordering of an
    already-validated, already-fetched subset - see get_ordered_idx.)

    Input:
        - id_list (list of int): positional indexes to check
        - meta_df (pandas DataFrame): metadata dataframe whose row count
            defines the valid index range
        - sort_id (bool): whether to actually perform the range check

    Output:
        None

    Raises:
        Exception listing the out-of-range indexes, if sort_id is True and
        any are found.
    """
    if sort_id:
        N = meta_df.shape[0]
        out_of_range_ids = [my_id for my_id in id_list if my_id < 0 or my_id >= N]
        if len(out_of_range_ids):
            msg = "some of indexes being used to subset the data are not valid max N:  {}  out_of_range_ids:  {}".format(N,
                                                                                                     out_of_range_ids)
            logger.error(msg)
            raise Exception("parse_gctx check_idx_validity " + msg)


def convert_ids_to_meta_type(id_list, meta_df):
    """
    Converts id_list's entries to the same dtype as meta_df's index, so that
    user-supplied ids (e.g. always strings) can be compared/looked-up
    correctly regardless of how the ids happen to be typed in the file.

    Input:
        - id_list (list): list of ids to convert
        - meta_df (pandas DataFrame): metadata dataframe whose index dtype
            id_list should be converted to

    Output:
        - a numpy array of id_list's values, cast to meta_df.index.dtype

    Raises:
        Exception if id_list's values can't be converted to meta_df.index's dtype.
    """
    try:
        return pd.Series(id_list).astype(meta_df.index.dtype).values
    except ValueError as ve:
        id_list_types = set([type(x) for x in id_list])
        msg = "The type of the id_list (rid or cid) being used to subset the data is not compatible with the metadata id's in the file.  Types found - meta_df.index.dtype:  {}  id_list_types:  {}".format(
            meta_df.index.dtype, id_list_types)
        logger.error(msg)
        raise Exception("parse_gctx check_if_ids_in_meta " + msg + "  ValueError ve:  {}".format(ve))


def get_ordered_idx(id_type, id_list, meta_df, sort_idx):
    """
    Gets positional index values corresponding to ids to subset by.

    Input:
        - id_type (str): either "id", "idx" or None. If None, id_list is
            ignored and all rows of meta_df are used.
        - id_list (list): either a list of positional indexes (id_type="idx"),
            a list of id names (id_type="id"), or ignored (id_type=None)
        - meta_df (dataframe): metadata dataframe used to look up positional
            indexes for id_type="id", or to determine the full range of
            indexes for id_type=None
        - sort_idx (bool): if True, return the sorted positional indexes to
            use for actually reading/subsetting the data (i.e. the indexes
            to fetch, in ascending order). If False, instead return the
            permutation that maps the sorted order back to id_list's
            original (as-requested) order - i.e. the indexes to apply to an
            already-sorted-and-fetched subset to restore the user's
            requested order.
    Output:
        - a list of indexes to subset a dimension by (None if meta_df is None)
    """
    if meta_df is not None:
        if id_type is None:
            id_list = range(0, len(list(meta_df.index)))
        elif id_type == "id":
            lookup = {x: i for (i,x) in enumerate(meta_df.index)}
            id_list = [lookup[str(i)] for i in id_list]
        if not sort_idx:
            return [sorted(id_list).index(i) for i in id_list] 
        return sorted(id_list)
    else:
        return None


def parse_metadata_df(dim, meta_group, convert_neg_666):
    """
    Reads in all metadata from .gctx file to pandas DataFrame
    with proper GCToo specifications.

    Each metadata field is read as its own HDF5 dataset. String-typed
    datasets are decoded using h5py's .asstr() accessor, which decodes each
    dataset according to whichever character encoding (ASCII or UTF-8) is
    recorded for that dataset in the file itself - the encoding is detected
    per-dataset (via h5py.check_string_dtype), not assumed, so this
    transparently supports gctx files written with either encoding.
    Non-string (numeric) datasets are read directly and then, like all
    columns, cast to str so that behavior is consistent with the gct
    parser (which reads the whole file as text); columns are subsequently
    converted back to numeric where possible.

    Input:
        - dim (str): Dimension of metadata; either "row" or "column"
        - meta_group (HDF5 group): Group from which to read metadata values
        - convert_neg_666 (bool): whether to convert "-666" values to np.nan or not
    Output:
        - meta_df (pandas DataFrame): data frame corresponding to metadata fields
            of dimension specified.
    """
    # read values from hdf5 & make a DataFrame
    header_values = {}
    array_index = 0
    for k in meta_group.keys():
        curr_dset = meta_group[k]
        if h5py.check_string_dtype(np.dtype(curr_dset.dtype)) is not None:
            # string columns are decoded according to whichever character
            # set (ascii or utf-8) is recorded in the file for this dataset
            temp_array = curr_dset.asstr()[:]
        else:
            temp_array = np.empty(curr_dset.shape, dtype=curr_dset.dtype)
            curr_dset.read_direct(temp_array)
        # convert all values to str in temp_array so that
        # to_numeric works consistently with gct and gct_x parser
        temp_array = temp_array.astype('str')
        header_values[str(k)] = temp_array
        array_index = array_index + 1


    meta_df = pd.DataFrame.from_dict(header_values)

    # save the ids for later use in the index; we do not want to convert them to
    # numeric
    ids = meta_df["id"].copy()
    del meta_df["id"]

    # Convert metadata to numeric if possible, after converting everything to string first
    # Note: This conversion first to string is to ensure consistent behavior between
    #    the gctx and gct parser (which by default reads the entire text file into a string)
    for col in meta_df.columns:
        try:
            meta_df[col] = pd.to_numeric(meta_df[col], errors="raise")
        except ValueError:
            pass

    meta_df.set_index(pd.Index(ids, dtype=str), inplace=True)

    # Replace -666 and -666.0 with NaN; also replace "-666" if convert_neg_666 is True
    meta_df = replace_666(meta_df, convert_neg_666)

    # set index and columns appropriately
    set_metadata_index_and_column_names(dim, meta_df)
    return meta_df


def replace_666(meta_df, convert_neg_666):
    """ Replaces occurrences of the CMap null sentinel value in metadata.

    If convert_neg_666 is True, any of the values -666 (int), "-666" (str),
    or -666.0 (float) found in a column are replaced with numpy.nan (this
    covers the sentinel regardless of whether that metadata column ended up
    numeric or string-typed). If convert_neg_666 is False, numeric sentinel
    values (-666 or -666.0) are instead normalized to the string "-666",
    so that the sentinel is represented consistently as a string across
    columns.

    Args:
        meta_df (pandas df): metadata dataframe to process
        convert_neg_666 (bool): whether to convert sentinel values to
            numpy.nan (True) or normalize them to the string "-666" (False)
    Returns:
        out_df (pandas df): updated copy of meta_df
    """
    sentinel_values = [-666, "-666", -666.0]
    out_df = meta_df.copy()
    if convert_neg_666:
        with pd.option_context('future.no_silent_downcasting', True):
            for col in out_df.columns:
                if out_df[col].isin(sentinel_values).any():
                    out_df[col] = out_df[col].replace(sentinel_values, np.nan).infer_objects(copy=False)
    else:
        for col in out_df.columns:
            if out_df[col].isin([-666, -666.0]).any():
                out_df[col] = out_df[col].replace([-666, -666.0], "-666")
    return out_df


def set_metadata_index_and_column_names(dim, meta_df):
    """
    Sets index and column names to GCTX convention.
    Input:
        - dim (str): Dimension of metadata to read. Must be either "row" or "col"
        - meta_df (pandas.DataFrame): data frame corresponding to metadata fields
            of dimension specified.
    Output:
        None
    """
    if dim == "row":
        meta_df.index.name = "rid"
        meta_df.columns.name = "rhd"
    elif dim == "col":
        meta_df.index.name = "cid"
        meta_df.columns.name = "chd"


def parse_data_df(data_dset, ridx, cidx, row_meta, col_meta):
    """
    Parses in data_df from hdf5, subsetting if specified.

    Input:
        -data_dset (h5py dset): HDF5 dataset from which to read data_df
        -ridx (list): list of indexes to subset from data_df
            (may be all of them if no subsetting)
        -cidx (list): list of indexes to subset from data_df
            (may be all of them if no subsetting)
        -row_meta (pandas DataFrame): the parsed in row metadata
        -col_meta (pandas DataFrame): the parsed in col metadata

    Output:
        - data_df (pandas DataFrame): the (possibly subsetted) data matrix,
            indexed by row_meta.index[ridx] and col_meta.index[cidx]. If
            subsetting is needed, whichever of the row/column dimensions
            would produce the smaller intermediate array is fetched from
            the HDF5 dataset first (h5py only supports fancy-indexing one
            dimension at a time).
    """
    total_rows = len(row_meta.index)
    total_cols = len(col_meta.index)
    if len(ridx) == total_rows and len(cidx) == total_cols:  # no subset
        data_array = np.empty(data_dset.shape, dtype=data_dset.dtype)
        data_dset.read_direct(data_array)
        data_array = data_array.transpose()
    else:
        # We can only subset on a single dimension at a time with h5py.
        # For the first dimension to use, pick the one that minimizes
        # the size of the intermediate array.
        row_first_count = total_cols * len(ridx)
        col_first_count = total_rows * len(cidx)

        if row_first_count < col_first_count:
            first_subset = data_dset[:, ridx].astype(data_dset.dtype)
            data_array = first_subset[cidx, :].transpose()
        else:
            first_subset = data_dset[cidx, :].astype(data_dset.dtype)
            data_array = first_subset[:, ridx].transpose()

    # make DataFrame instance
    data_df = pd.DataFrame(data_array, index=row_meta.index[ridx], columns=col_meta.index[cidx])
    return data_df


def get_column_metadata(gctx_file_path, convert_neg_666=True):
    """
    Opens .gctx file and returns only column metadata

    Input:
        Mandatory:
        - gctx_file_path (str): full path to gctx file you want to parse.

        Optional:
        - convert_neg_666 (bool): whether to convert -666 values to numpy.nan
            or not. Default = True.

    Output:
        - col_meta (pandas DataFrame): a DataFrame of all column metadata values.
    """
    full_path = os.path.expanduser(gctx_file_path)
    # open file
    gctx_file = h5py.File(full_path, "r")
    col_dset = gctx_file[col_meta_group_node]
    col_meta = parse_metadata_df("col", col_dset, convert_neg_666)
    gctx_file.close()
    return col_meta


def get_row_metadata(gctx_file_path, convert_neg_666=True):
    """
    Opens .gctx file and returns only row metadata

    Input:
        Mandatory:
        - gctx_file_path (str): full path to gctx file you want to parse.

        Optional:
        - convert_neg_666 (bool): whether to convert -666 values to numpy.nan
            or not. Default = True.

    Output:
        - row_meta (pandas DataFrame): a DataFrame of all row metadata values.
    """
    full_path = os.path.expanduser(gctx_file_path)
    # open file
    gctx_file = h5py.File(full_path, "r")
    row_dset = gctx_file[row_meta_group_node]
    row_meta = parse_metadata_df("row", row_dset, convert_neg_666)
    gctx_file.close()
    return row_meta
