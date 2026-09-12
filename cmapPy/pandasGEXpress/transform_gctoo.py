"""
transform_gctoo.py

module to contain various transformations of GCToo objects.  Initially just transpose.

"""
import logging

import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger
import cmapPy.pandasGEXpress.GCToo as GCToo


logger = logging.getLogger(setup_logger.LOGGER_NAME)

def transpose(my_gctoo):
    """ Transpose a GCToo object: swap the roles of rows and columns.

    The data matrix is transposed, and the row and column metadata dfs are
    swapped with each other (the original row_metadata_df becomes the new
    col_metadata_df, and vice versa).

    Input:
        - my_gctoo (GCToo): a GCToo instance

    Output:
        - new_gctoo (GCToo): a new GCToo instance with data_df transposed
            and row/col metadata dfs swapped
    """
    new_gctoo = GCToo.GCToo(
        data_df=my_gctoo.data_df.T,
        row_metadata_df=my_gctoo.col_metadata_df,
        col_metadata_df=my_gctoo.row_metadata_df
    )

    return new_gctoo