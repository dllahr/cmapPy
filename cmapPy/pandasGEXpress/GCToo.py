"""
DATA:
-----------------------------
|  |          cid           |
-----------------------------
|  |                        |
|r |                        |
|i |          data          |
|d |                        |
|  |                        |
-----------------------------
ROW METADATA:
--------------------------
|id|        rhd          |
--------------------------
|  |                     |
|r |                     |
|i |    row_metadata     |
|d |                     |
|  |                     |
--------------------------
COLUMN METADATA:
N.B. The df is transposed from how it looks in a gct file.
---------------------
|id|      chd       |
---------------------
|  |                |
|  |                |
|  |                |
|c |                |
|i |  col_metadata  |
|d |                |
|  |                |
|  |                |
|  |                |
---------------------

N.B. rids, cids, rhds, and chds must be:
- unique
- matching in both content & order everywhere they're found
"""
import numpy as np
import pandas as pd
import logging
import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger


__authors__ = 'Oana Enache, Lev Litichevskiy, Dave Lahr'
__email__ = 'dlahr@broadinstitute.org'


class GCToo(object):
    """Class representing parsed gct(x) objects as pandas dataframes.

    This is the central data structure of cmapPy: every parsed .gct/.gctx
    file is returned as a GCToo instance, and every file written by
    write_gct/write_gctx expects one as input. A GCToo bundles together
    3 component pandas DataFrames that describe a single dataset:
        - data_df: the numeric data matrix. Rows are indexed by "rid"
          (row/probe/gene ids), columns are indexed by "cid" (column/
          sample ids).
        - row_metadata_df: annotations for each row, indexed by "rid";
          column names are the row headers ("rhd").
        - col_metadata_df: annotations for each column, indexed by "cid";
          column names are the column headers ("chd"). N.B. this df is
          the transpose of how column metadata is laid out in a gct file
          (here, cids are rows).
    An optional 4th attribute, multi_index_df, combines all 3 of the
    above into a single pandas DataFrame with a MultiIndex for both rows
    and columns (see assemble_multi_index_df).

    Invariants enforced automatically (via __setattr__, every time
    data_df, row_metadata_df, or col_metadata_df is assigned):
        - each of the 3 component dataframes must have unique index and
          column values (checked by check_df)
        - the rid values in row_metadata_df.index must exactly match (as
          a set) the rid values in data_df.index; likewise cid values in
          col_metadata_df.index must match data_df.columns (checked by
          id_match_check)
        - row_metadata_df and col_metadata_df are automatically reindexed
          to match the order of data_df.index / data_df.columns, so the
          3 dataframes always agree in both content and order
        - multi_index_df cannot be reassigned once a GCToo has been
          constructed; to get a new one, build a new GCToo instance

    N.B. CMap null convention: metadata fields use the sentinel value
    -666 (not NaN) to represent missing/null values. Parsers accept a
    convert_neg_666 flag to convert -666 to numpy.nan on read, and
    writers accept a convert_back_to_neg_666 flag to convert numpy.nan
    back to -666 on write.
    """
    def __init__(self, data_df, row_metadata_df=None, col_metadata_df=None,
                 src=None, version=None, make_multiindex=False, logger_name=setup_logger.LOGGER_NAME):
        """Construct a GCToo instance from a data matrix and optional metadata.

        Input:
            Mandatory:
            - data_df (pandas DataFrame): the numeric data matrix; index
                values are rids, column values are cids.

            Optional:
            - row_metadata_df (pandas DataFrame): row metadata, indexed by
                rid, with row headers (rhd) as columns. Default=None, in
                which case an empty DataFrame (index = data_df.index, no
                columns) is used.
            - col_metadata_df (pandas DataFrame): column metadata, indexed
                by cid, with column headers (chd) as columns. Default=None,
                in which case an empty DataFrame (index = data_df.columns,
                no columns) is used.
            - src (str): a label for where this GCToo came from, e.g. the
                path of the file it was parsed from. Default=None.
            - version (str): a label for the GCT(X) format version this
                object corresponds to, e.g. "GCTX1.0". Default=None.
            - make_multiindex (bool): whether to also assemble
                multi_index_df at construction time. Default=False.
            - logger_name (str): name of the logger to use. Default is
                cmapPy's standard logger name.

        Output:
            None (the constructed GCToo instance is self).

        Raises:
            Exception if data_df is not a pandas DataFrame, if any of the
            3 component dataframes has non-unique index/column values, or
            if row_metadata_df/col_metadata_df ids don't match data_df's
            ids (see check_df and id_match_check).
        """
        self.logger = logging.getLogger(logger_name)

        self.src = src
        self.version = version

        # Check data_df before setting
        self.check_df(data_df)
        self.data_df = data_df

        if row_metadata_df is None:
            self.row_metadata_df = pd.DataFrame(index=data_df.index)
        else:
            # Lots of checks will occur when this attribute is set (see __setattr__ below)
            self.row_metadata_df = row_metadata_df

        if col_metadata_df is None:
            self.col_metadata_df = pd.DataFrame(index=data_df.columns)
        else:
            # Lots of checks will occur when this attribute is set (see __setattr__ below)
            self.col_metadata_df = col_metadata_df

        # Create multi_index_df if explicitly requested
        if make_multiindex:
            self.assemble_multi_index_df()
        else:
            self.multi_index_df = None

        # This GCToo object is now initialized
        self._initialized = True

    def __setattr__(self, name, value):
        """Override to enforce GCToo's invariants whenever a component
        dataframe is (re)assigned.

        - Assigning row_metadata_df or col_metadata_df validates it
          (check_df), checks that its ids match data_df (id_match_check),
          and reindexes it to data_df's row/column order before storing.
        - Reassigning data_df after initial construction checks that the
          existing row_metadata_df/col_metadata_df ids still match, then
          reindexes both metadata dataframes to the new data_df's order.
        - Reassigning multi_index_df after initial construction is
          disallowed (raises an Exception); build a new GCToo instance
          instead.
        - Any other attribute is set normally.
        """
        # Make sure row/col metadata agree with data_df before setting
        if name in ["row_metadata_df", "col_metadata_df"]:
            self.check_df(value)
            if name == "row_metadata_df":
                self.id_match_check(self.data_df, value, "row")
                value = value.reindex(self.data_df.index)
                super(GCToo, self).__setattr__(name, value)
            else:
                self.id_match_check(self.data_df, value, "col")
                value = value.reindex(self.data_df.columns)
                super(GCToo, self).__setattr__(name, value)

        # When reassigning data_df after initialization, reindex row/col metadata if necessary
        # N.B. Need to check if _initialized is present before checking if it's true, or code will break
        elif name == "data_df" and "_initialized" in self.__dict__ and self._initialized:
            self.id_match_check(value, self.row_metadata_df, "row")
            self.id_match_check(value, self.col_metadata_df, "col")
            super(GCToo, self).__setattr__("row_metadata_df", self.row_metadata_df.reindex(value.index))
            super(GCToo, self).__setattr__("col_metadata_df", self.col_metadata_df.reindex(value.columns))
            super(GCToo, self).__setattr__(name, value)

        # Can't reassign multi_index_df after initialization
        elif name == "multi_index_df" and "_initialized" in self.__dict__ and self._initialized:
            msg = ("Cannot reassign value of multi_index_df attribute; "  +
                "if you'd like a new multiindex df, please create a new GCToo instance" +
                "with appropriate data_df, row_metadata_df, and col_metadata_df fields.")
            self.logger.error(msg)
            raise Exception("GCToo.__setattr__: " + msg)

        # Otherwise, use the normal __setattr__ method
        else:
            super(GCToo, self).__setattr__(name, value)

    def check_df(self, df):
        """
        Verifies that df is a pandas DataFrame instance and
        that its index and column values are unique.

        Input:
            - df: object to check (expected to be a pandas DataFrame).

        Output:
            - True if df is a DataFrame with unique index and column
                values.

        Raises:
            Exception if df is not a pandas DataFrame, or if its index or
            columns contain duplicate values (the error message lists the
            offending entries).
        """
        if isinstance(df, pd.DataFrame):
            if not df.index.is_unique:
                repeats = df.index[df.index.duplicated()].values
                msg = "Index values must be unique but aren't. The following entries appear more than once: {}".format(repeats)
                self.logger.error(msg)
                raise Exception("GCToo GCToo.check_df " + msg)
            if not df.columns.is_unique:
                repeats = df.columns[df.columns.duplicated()].values
                msg = "Columns values must be unique but aren't. The following entries appear more than once: {}".format(repeats)
                self.logger.error(msg)
                raise Exception("GCToo GCToo.check_df " + msg)
            else:
                return True
        else:
            msg = "expected Pandas DataFrame, got something else:  {}  of type:  {}".format(df, type(df))
            self.logger.error(msg)
            raise Exception("GCToo GCToo.check_df " + msg)

    def id_match_check(self, data_df, meta_df, dim):
        """
        Verifies that id values match between:
            - row case: index of data_df & index of row metadata
            - col case: columns of data_df & index of column metadata

        Input:
            - data_df (pandas DataFrame): the data matrix to check against.
            - meta_df (pandas DataFrame): row_metadata_df (if dim="row") or
                col_metadata_df (if dim="col") to check.
            - dim (str): either "row" or "col"; determines whether
                data_df.index or data_df.columns is compared to
                meta_df.index.

        Output:
            - True if the ids match (same count and same set of values).

        Raises:
            Exception (with both sets of ids in the message) if the ids
            don't match.
        """
        if dim == "row":
            if len(data_df.index) == len(meta_df.index) and set(data_df.index) == set(meta_df.index):
                return True
            else:
                msg = ("The rids are inconsistent between data_df and row_metadata_df.\n" +
                 "data_df.index.values:\n{}\nrow_metadata_df.index.values:\n{}").format(data_df.index.values, meta_df.index.values)
                self.logger.error(msg)
                raise Exception("GCToo GCToo.id_match_check " + msg)
        elif dim == "col":
            if len(data_df.columns) == len(meta_df.index) and set(data_df.columns) == set(meta_df.index):
                return True
            else:
                msg = ("The cids are inconsistent between data_df and col_metadata_df.\n" +
                 "data_df.columns.values:\n{}\ncol_metadata_df.index.values:\n{}").format(data_df.columns.values, meta_df.index.values)
                self.logger.error(msg)
                raise Exception("GCToo GCToo.id_match_check " + msg)

    def __str__(self):
        """Prints a string representation of a GCToo object."""
        version = "{}\n".format(self.version)
        source = "src: {}\n".format(self.src)


        data = "data_df: [{} rows x {} columns]\n".format(
        self.data_df.shape[0], self.data_df.shape[1])

        row_meta = "row_metadata_df: [{} rows x {} columns]\n".format(
        self.row_metadata_df.shape[0], self.row_metadata_df.shape[1])

        col_meta = "col_metadata_df: [{} rows x {} columns]".format(
        self.col_metadata_df.shape[0], self.col_metadata_df.shape[1])

        full_string = (version + source + data + row_meta + col_meta)
        return full_string

    def assemble_multi_index_df(self):
        """Assembles three component dataframes into a multiindex dataframe.
        Sets the result to self.multi_index_df.
        IMPORTANT: Cross-section ("xs") is the best command for selecting
        data. Be sure to use the flag "drop_level=False" with this command,
        or else the dataframe that is returned will not have the same
        metadata as the input.
        N.B. "level" means metadata header.
        N.B. "axis=1" indicates column annotations.
        Examples:
            1) Select the probe with pr_lua_id="LUA-3404":
            lua3404_df = multi_index_df.xs("LUA-3404", level="pr_lua_id", drop_level=False)
            2) Select all DMSO samples:
            DMSO_df = multi_index_df.xs("DMSO", level="pert_iname", axis=1, drop_level=False)
        """
        #prepare row index
        self.logger.debug("Row metadata shape: {}".format(self.row_metadata_df.shape))
        self.logger.debug("Is empty? {}".format(self.row_metadata_df.empty))
        row_copy = pd.DataFrame(self.row_metadata_df.index) if self.row_metadata_df.empty else self.row_metadata_df.copy()
        row_copy["rid"] = row_copy.index
        row_index = pd.MultiIndex.from_arrays(row_copy.T.values, names=row_copy.columns)

        #prepare column index
        self.logger.debug("Col metadata shape: {}".format(self.col_metadata_df.shape))
        col_copy = pd.DataFrame(self.col_metadata_df.index) if self.col_metadata_df.empty else self.col_metadata_df.copy()
        col_copy["cid"] = col_copy.index
        transposed_col_metadata = col_copy.T
        col_index = pd.MultiIndex.from_arrays(transposed_col_metadata.values, names=transposed_col_metadata.index)

        # Create multi index dataframe using the values of data_df and the indexes created above
        self.logger.debug("Data df shape: {}".format(self.data_df.shape))
        self.multi_index_df = pd.DataFrame(data=self.data_df.values, index=row_index, columns=col_index)


def multi_index_df_to_component_dfs(multi_index_df, rid="rid", cid="cid"):
    """ Convert a multi-index df (as assembled by GCToo.assemble_multi_index_df)
    back into 3 component dfs: data_df, row_metadata_df, and col_metadata_df.

    Input:
        Mandatory:
        - multi_index_df (pandas DataFrame): a dataframe whose index and/or
            columns are pandas MultiIndex objects, one level of which is
            named by the rid/cid arguments (row/column ids) and the
            remaining levels are row/column metadata headers (rhd/chd).
            If the index (or columns) is not actually a MultiIndex, or
            has only a single level, the corresponding metadata df will
            have no columns (i.e. no metadata headers).

        Optional:
        - rid (str): name of the row id level within multi_index_df's
            (row) index. Default = "rid".
        - cid (str): name of the column id level within multi_index_df's
            column index. Default = "cid".

    Output:
        - data_df (pandas DataFrame): the numeric data matrix, indexed by
            rid/cid.
        - row_metadata_df (pandas DataFrame): row metadata extracted from
            the non-rid levels of multi_index_df's index, indexed by rid.
        - col_metadata_df (pandas DataFrame): column metadata extracted
            from the non-cid levels of multi_index_df's columns, indexed
            by cid.
    """

    # Id level of the multiindex will become the index
    rids = list(multi_index_df.index.get_level_values(rid))
    cids = list(multi_index_df.columns.get_level_values(cid))

    # It's possible that the index and/or columns of multi_index_df are not
    # actually multi-index; need to check for this and there are more than one level in index(python3)
    if isinstance(multi_index_df.index, pd.MultiIndex):

        # check if there are more than one levels in index (python3)
        if len(multi_index_df.index.names) > 1:

            # If so, drop rid because it won't go into the body of the metadata
            mi_df_index = multi_index_df.index.droplevel(rid)

            # Names of the multiindex levels become the headers
            rhds = list(mi_df_index.names)

            # Assemble metadata values
            row_metadata = np.array([mi_df_index.get_level_values(level).values for level in list(rhds)]).T

        # if there is one level in index (python3), then rhds and row metadata should be empty
        else:
            rhds = []
            row_metadata = []

    # If the index is not multi-index, then rhds and row metadata should be empty
    else:
        rhds = []
        row_metadata = []

    # Check if columns of multi_index_df are in fact multi-index
    if isinstance(multi_index_df.columns, pd.MultiIndex):

        # Check if there are more than one levels in columns(python3)
        if len(multi_index_df.columns.names) > 1:

            # If so, drop cid because it won't go into the body of the metadata
            mi_df_columns = multi_index_df.columns.droplevel(cid)

            # Names of the multiindex levels become the headers
            chds = list(mi_df_columns.names)

            # Assemble metadata values
            col_metadata = np.array([mi_df_columns.get_level_values(level).values for level in list(chds)]).T

        # If there is one level in columns (python3), then rhds and row metadata should be empty
        else:
            chds = []
            col_metadata = []
    # If the columns are not multi-index, then rhds and row metadata should be empty
    else:
        chds = []
        col_metadata = []

    # Create component dfs
    row_metadata_df = pd.DataFrame.from_records(row_metadata, index=pd.Index(rids, name="rid"), columns=pd.Index(rhds, name="rhd"))
    col_metadata_df = pd.DataFrame.from_records(col_metadata, index=pd.Index(cids, name="cid"), columns=pd.Index(chds, name="chd"))
    data_df = pd.DataFrame(multi_index_df.values, index=pd.Index(rids, name="rid"), columns=pd.Index(cids, name="cid"))

    return data_df, row_metadata_df, col_metadata_df
