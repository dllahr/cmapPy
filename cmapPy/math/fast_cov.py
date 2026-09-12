import logging
import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger
import numpy


logger = logging.getLogger(setup_logger.LOGGER_NAME)


def _fast_dot_divide(x, y, destination):
    """helper method for use within the _fast_cov method - carry out the dot product and subsequent 
    division to generate the covariance values.  For use when there are no missing values.
    """
    numpy.dot(x.T, y, out=destination)
    numpy.divide(destination, (x.shape[0] - 1), out=destination)


def calculate_non_mask_overlaps(x_mask, y_mask):
    """for two boolean mask arrays x_mask (MxN) and y_mask (MxP), determine, for each pair of columns (one
    from x_mask, one from y_mask), the number of rows that are unmasked in both - i.e. the number of entries
    that would overlap (be simultaneously non-missing) if the corresponding data columns' dot product were taken.

    Args:
        x_mask (numpy array-like boolean) MxN
        y_mask (numpy array-like boolean) MxP; must have the same number of rows as x_mask

    Returns:
        (numpy array-like) NxP array of overlap counts
    """
    x_is_not_nan = 1 * ~x_mask
    y_is_not_nan = 1 * ~y_mask

    r = numpy.dot(x_is_not_nan.T, y_is_not_nan)
    return r


def _nan_dot_divide(x, y, destination):
    """helper method for use within the _fast_cov method - carry out the dot product and subsequent
    division to generate the covariance values.  For use when there are missing values.
    """
    numpy.ma.dot(x.T, y, out=destination)

    divisor = calculate_non_mask_overlaps(x.mask, y.mask) - 1

    numpy.ma.divide(destination, divisor, out=destination)


def fast_cov(x, y=None, destination=None):
    """calculate the covariance matrix for the columns of x (MxN), or optionally, the covariance matrix between the
    columns of x and and the columns of y (MxP).  (In the language of statistics, the columns are variables, the rows
    are observations).

    Args:
        x (numpy array-like) MxN in shape
        y (numpy array-like) MxP in shape
        destination (numpy array-like) optional location where to store the results as they are calculated (e.g. a numpy
            memmap of a file)

        returns (numpy array-like) array of the covariance values
            for defaults (y=None), shape is NxN
            if y is provided, shape is NxP
    """
    r = _fast_cov(numpy.mean, _fast_dot_divide, x, y, destination)

    return r


def _fast_cov(mean_method, dot_divide_method, x, y, destination):
    """internal implementation shared by fast_cov and nan_fast_cov: validates x, y, and destination; reshapes
    1-D x/y into column vectors; mean-centers x and y using mean_method (e.g. numpy.mean or numpy.nanmean,
    letting the caller choose nan-tolerant behavior); allocates a zeros destination if one was not provided;
    and calls dot_divide_method to compute the covariance values into destination.

    Returns:
        destination (numpy array-like) the (possibly newly allocated) destination, filled with the
            covariance values
    """
    validate_inputs(x, y, destination)

    new_x = x if len(x.shape) == 2 else x[:, numpy.newaxis]

    if y is None:
        y = new_x
    new_y = y if len(y.shape) == 2 else y[:, numpy.newaxis]

    if destination is None:
        destination = numpy.zeros((new_x.shape[1], new_y.shape[1]))

    mean_x = mean_method(new_x, axis=0)
    mean_y = mean_method(new_y, axis=0)

    mean_centered_x = (new_x - mean_x).astype(destination.dtype)
    mean_centered_y = (new_y - mean_y).astype(destination.dtype)
    
    dot_divide_method(mean_centered_x, mean_centered_y, destination)

    return destination


def validate_inputs(x, y, destination):
    """validate the x, y, and destination arguments used by fast_cov / nan_fast_cov (via _fast_cov), raising
    an exception describing every problem found if any of the following do not hold:
        - x is numpy array-like (has a "shape" attribute)
        - if destination is provided, it is numpy array-like (has a "shape" attribute)
        - if y is None: when destination is provided, its shape is (N, N) where N is the number of columns
          of x (or 1 if x is 1-D)
        - if y is provided: y is numpy array-like, x and y have the same number of rows, and (when
          destination is provided) destination's shape is (number of columns of x, number of columns of y)

    Args:
        x (numpy array-like) MxN in shape
        y (numpy array-like, optional) MxP in shape
        destination (numpy array-like, optional) location where results would be stored

    Returns:
        None

    Raises:
        CmapPyMathFastCovInvalidInputXY: if any of the conditions above are violated; the exception message
            describes every problem found
    """
    error_msg = ""

    if not hasattr(x, "shape"):
        error_msg += "x needs to be numpy array-like but it does not have \"shape\" attribute - type(x):  {}\n".format(type(x))
    
    if destination is not None and not hasattr(destination, "shape"):
        error_msg += "destination needs to be numpy array-like but it does not have \"shape\" attribute - type(destination):  {}\n".format(type(destination))

    if y is None:
        if destination is not None:
            expected_dim = x.shape[1] if len(x.shape) == 2 else 1
            expected_shape = (expected_dim, expected_dim)
            if destination.shape != expected_shape:
                error_msg += "x and destination provided, therefore destination must have shape matching number of columns of x but it does not - x.shape:  {}  expected_shape:  {}  destination.shape:  {}\n".format(
                    x.shape, expected_shape, destination.shape)
    else:
        if not hasattr(y, "shape"):
            error_msg += "y needs to be numpy array-like but it does not have \"shape\" attribute - type(y):  {}\n".format(type(y))
        elif x.shape[0] != y.shape[0]:
            error_msg += "the number of rows in the x and y matrices must be the same - x.shape:  {}  y.shape:  {}\n".format(x.shape, y.shape)
        elif destination is not None:
            expected_rows = x.shape[1] if len(x.shape) == 2 else 1
            expected_cols = y.shape[1] if len(y.shape) == 2 else 1
            expected_shape = (expected_rows, expected_cols)
            if destination.shape != expected_shape:
                error_msg += "x, y, and destination provided, therefore destination must have number of rows matching number of columns of x and destination needs to have number of columns matching number of columns of y - x.shape:  {}  y.shape:  {}  expected_shape:  {}  destination.shape:  {}\n".format(
                    x.shape, y.shape, expected_shape, destination.shape)

    if error_msg != "":
        raise CmapPyMathFastCovInvalidInputXY(error_msg)


def nan_fast_cov(x, y=None, destination=None):
    """calculate the covariance matrix (ignoring nan values) for the columns of x (MxN), or optionally, the covariance matrix between the
    columns of x and and the columns of y (MxP).  (In the language of statistics, the columns are variables, the rows
    are observations). For each pair of columns, only the rows where neither value is nan are used, so
    different entries of the result may effectively be computed from different numbers of observations (the
    pairwise non-nan overlap count, minus 1); entries whose overlap count is 0 or 1 (a non-positive divisor)
    are set to nan.

    Args:
        x (numpy array-like) MxN in shape
        y (numpy array-like) MxP in shape
        destination (numpy masked array-like) optional location where to store the results as they are calculated (e.g. a numpy
            memmap of a file); if provided, the return value is this (possibly still masked) destination
            array; if not provided, a new plain (non-masked) numpy array is returned with masked/invalid
            entries filled with nan

        returns (numpy array-like) array of the covariance values
            for defaults (y=None), shape is NxN
            if y is provided, shape is NxP
    """
    x_masked = numpy.ma.array(x, mask=numpy.isnan(x))

    if y is None:
        y_masked = x_masked
    else:
        y_masked = numpy.ma.array(y, mask=numpy.isnan(y))

    dest_was_None = False
    if destination is None:
        num_rows = x_masked.shape[1] if len(x_masked.shape) == 2 else 1
        num_cols = y_masked.shape[1] if len(y_masked.shape) == 2 else 1
        destination = numpy.ma.zeros((num_rows, num_cols))
        dest_was_None = True

    r = _fast_cov(numpy.nanmean, _nan_dot_divide, x_masked, y_masked, destination)

    r[numpy.isinf(r)] = numpy.nan

    r = numpy.ma.filled(r, fill_value=numpy.nan) if dest_was_None else r

    return r


class CmapPyMathFastCovInvalidInputXY(Exception):
    """Raised by validate_inputs (used within fast_cov / nan_fast_cov) when x, y, and/or destination do not
    have the expected types (numpy array-like) or compatible shapes."""
    pass
