import logging
import h5py
import numpy
import cmapPy.pandasGEXpress.setup_GCToo_logger as setup_logger

__author__ = "Oana Enache"
__email__ = "oana@broadinstitute.org"

logger = logging.getLogger(setup_logger.LOGGER_NAME)

src_attr = "src"
data_matrix_node = "/0/DATA/0/matrix"
row_meta_group_node = "/0/META/ROW"
col_meta_group_node = "/0/META/COL"
version_attr = "version"
version_number = "GCTX1.0"


def write(gctoo_object, out_file_name, convert_back_to_neg_666=True, gzip_compression_level=6,
    max_chunk_kb=1024, matrix_dtype=numpy.float32, data_compression_level=4):
    """
	Writes a GCToo instance to specified file.

	Input:
		- gctoo_object (GCToo): A GCToo instance.
		- out_file_name (str): file name to write gctoo_object to.
        - convert_back_to_neg_666 (bool): whether to convert np.NAN in metadata back to "-666",
            as per the CMap metadata null convention. Default = True.
        - gzip_compression_level (int, default=6): Compression level to use for metadata.
        - max_chunk_kb (int, default=1024): The maximum number of KB a given chunk will occupy
        - matrix_dtype (numpy dtype, default=numpy.float32): Storage data type for data matrix.
            NB use numpy.bool_ instead numpy.bool, numnpy.int_ instead numpy.int.
            See https://numpy.org/doc/stable/user/basics.types.html for list of types
        - data_compression_level (int, default=4): Compression level to use for data. Default value
            of 4 corresponds to hdf5 default.

	Output:
		None (writes gctoo_object to out_file_name, with a ".gctx" suffix
		appended if not already present).
	"""
    # make sure out file has a .gctx suffix
    gctx_out_name = add_gctx_to_out_name(out_file_name)

    # open an hdf5 file to write to
    hdf5_out = h5py.File(gctx_out_name, "w")

    # write version
    write_version(hdf5_out)

    # write src
    write_src(hdf5_out, gctoo_object, gctx_out_name)

    # set chunk size for data matrix
    elem_per_kb = calculate_elem_per_kb(max_chunk_kb, matrix_dtype)
    chunk_size = set_data_matrix_chunk_size(gctoo_object.data_df.shape, max_chunk_kb, elem_per_kb)

    # write data matrix
    data_df = check_fix_metadata(gctoo_object.data_df)
    hdf5_out.create_dataset(data_matrix_node, data=data_df.transpose().values,
        dtype=matrix_dtype, compression=data_compression_level)

    # write col metadata
    col_metadata_df = check_fix_metadata(gctoo_object.col_metadata_df)
    write_metadata(hdf5_out, "col", col_metadata_df, convert_back_to_neg_666,
        gzip_compression=gzip_compression_level)

    # write row metadata
    row_metadata_df = check_fix_metadata(gctoo_object.row_metadata_df)
    write_metadata(hdf5_out, "row", row_metadata_df, convert_back_to_neg_666,
        gzip_compression=gzip_compression_level)

    # close gctx file
    hdf5_out.close()


def add_gctx_to_out_name(out_file_name):
    """
	If there isn't a '.gctx' suffix to specified out_file_name, it adds one.

	Input:
		- out_file_name (str): the file name to write gctx-formatted output to.
			(Can end with ".gctx" or not)

	Output:
		- out_file_name (str): the file name to write gctx-formatted output to, with ".gctx" suffix
	"""
    if not out_file_name.endswith(".gctx"):
        out_file_name = out_file_name + ".gctx"
    return out_file_name


def write_src(hdf5_out, gctoo_object, out_file_name):
    """
	Writes src as attribute of gctx out file. 

	Input:
		- hdf5_out (h5py): hdf5 file to write to
		- gctoo_object (GCToo): GCToo instance to be written to .gctx
		- out_file_name (str): name of hdf5 out file. Used as the src
			attribute if gctoo_object.src is None.

	Output:
		None
	"""
    if gctoo_object.src == None:
        hdf5_out.attrs[src_attr] = out_file_name
    else:
        hdf5_out.attrs[src_attr] = gctoo_object.src


def write_version(hdf5_out):
    """
	Writes version as attribute of gctx out file. 

	Input:
		- hdf5_out (h5py): hdf5 file to write to

	Output:
		None
	"""
    hdf5_out.attrs[version_attr] = numpy.bytes_(version_number)

def calculate_elem_per_kb(max_chunk_kb, matrix_dtype):
    """
    Calculates the number of elem per kb depending on the max chunk size set. 

    Input: 
        - max_chunk_kb (int, default=1024): The maximum number of KB a given chunk will occupy
        - matrix_dtype (numpy dtype, default=numpy.float32): Storage data type for data matrix

    Returns: 
        elem_per_kb (int), the number of elements per kb for matrix dtype specified. 
    """

    matrix_dtype_itemsize = matrix_dtype(1).itemsize
    logger.debug("matrix_dtype_itemsize:  {}".format(matrix_dtype_itemsize))

    return max_chunk_kb / matrix_dtype_itemsize


def set_data_matrix_chunk_size(df_shape, max_chunk_kb, elem_per_kb):
    """
    Sets chunk size to use for writing data matrix. 
    Note. Calculation used here is for compatibility with cmapM and cmapR. 

    Input:
        - df_shape (tuple): shape of input data_df. 
        - max_chunk_kb (int, default=1024): The maximum number of KB a given chunk will occupy
        - elem_per_kb (int): Number of elements per kb 

    Returns:
        chunk size (tuple) to use for chunking the data matrix 
    """ 
    row_chunk_size = min(df_shape[0], 1000)
    col_chunk_size = min(((max_chunk_kb*elem_per_kb)//row_chunk_size), df_shape[1])
    return (row_chunk_size, col_chunk_size)

def write_metadata(hdf5_out, dim, metadata_df, convert_back_to_neg_666, gzip_compression):
    """
	Writes either column or row metadata to proper node of gctx out (hdf5) file.

	The "id" field is always written as its own utf-8 string dataset. Each
	remaining metadata column (other than a column literally named "ind",
	which is skipped) is written as its own dataset: string/object-dtype
	columns are written via write_string_dataset (utf-8 encoded); other
	(numeric) columns are written directly, downcasting float64 to
	float32 and int64 to int32 first (for compatibility/compactness).

	Input:
		- hdf5_out (h5py): open hdf5 file to write to
		- dim (str; must be "row" or "col"): dimension of metadata to write to
		- metadata_df (pandas DataFrame): metadata DataFrame to write to file
		- convert_back_to_neg_666 (bool): Whether to convert numpy.nans back to "-666",
				as per CMap metadata null convention
		- gzip_compression (int): gzip compression level to use for each metadata dataset

	Output:
		None
	"""
    if dim == "col":
        hdf5_out.create_group(col_meta_group_node)
        metadata_node_name = col_meta_group_node
    elif dim == "row":
        hdf5_out.create_group(row_meta_group_node)
        metadata_node_name = row_meta_group_node
    else:
        logger.error("'dim' argument must be either 'row' or 'col'!")

    # write id field to expected node
    write_string_dataset(hdf5_out, metadata_node_name + "/id", "id",
        [str(x) for x in metadata_df.index], gzip_compression)

    metadata_fields = list(metadata_df.columns.copy())

    # if specified, convert numpy.nans in metadata back to -666
    if convert_back_to_neg_666:
        for c in metadata_fields:
            metadata_df[[c]] = metadata_df[[c]].replace([numpy.nan], ["-666"])

    # write metadata columns to their own arrays
    for field in [entry for entry in metadata_fields if entry != "ind"]:
        if numpy.array(metadata_df.loc[:, field]).dtype.type in (numpy.str_, numpy.object_):
            array_write = [str(x) for x in metadata_df.loc[:, field]]
            write_string_dataset(hdf5_out, metadata_node_name + "/" + field, field,
                array_write, gzip_compression)
        else:
            array_write = numpy.array(metadata_df.loc[:, field])
            if array_write.dtype == numpy.float64:
                array_write = array_write.astype(numpy.float32)
            elif array_write.dtype == numpy.int64:
                array_write = array_write.astype(numpy.int32)
            hdf5_out.create_dataset(metadata_node_name + "/" + field,
                                    data=array_write,
                                    compression=gzip_compression)


def write_string_dataset(hdf5_out, dataset_path, field_name, values, gzip_compression):
    """
    Writes a list of strings to hdf5_out as a utf-8 encoded string dataset. If any value
    cannot be encoded as utf-8 (e.g. it contains a lone surrogate code point), raises an
    Exception identifying the field and entry responsible, rather than a generic error
    from h5py/numpy.

    Input:
        - hdf5_out (h5py): open hdf5 file to write to
        - dataset_path (str): full node path to create the dataset at
        - field_name (str): name of the metadata field (or "id"), used only for error messages
        - values (list of str): the values to write
        - gzip_compression (int): compression level to use

    Output:
        None
    """
    try:
        hdf5_out.create_dataset(dataset_path, data=values,
            dtype=h5py.string_dtype(encoding="utf-8"), compression=gzip_compression)
    except UnicodeEncodeError:
        for i, value in enumerate(values):
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as e:
                msg = "could not encode this metadata entry as utf-8 - field:  {}  i:  {}  value:  {}  error:  {}".format(
                    field_name, i, value, e)
                logger.exception(msg)
                raise Exception(msg)


def check_fix_metadata(metadata_df):
    """
    Sanitizes a dataframe's index and column labels for writing to HDF5:
    forward slash ("/") is not allowed in gctx (HDF5) node names, since it
    is the path separator, so any "/" found in an index or column label is
    replaced with "|" (a warning is logged for each replacement made).

    Input:
        - metadata_df (pandas DataFrame): dataframe whose index and/or
            columns may contain "/" characters (this is used both for
            data_df, whose index/columns are rid/cid, and for the row/col
            metadata dataframes, whose index is rid/cid).

    Output:
        - new_metadata_df (pandas DataFrame): a copy of metadata_df with
            "/" replaced with "|" in its index and column labels.
    """
    work_on = [
        ("column", metadata_df.columns), ("index", metadata_df.index)
    ]

    results = []
    for name, generic_index in work_on:
        new_list = generic_index.to_list()
        results.append(new_list)

        for i, gnrc_indx in enumerate(new_list):
            if "/" in gnrc_indx:
                new_gnrc_indx = gnrc_indx.replace("/", "|")
                logger.warning("forward slash / character in {} of metadata_df is not allowed in hdf5 gctx - will be replaced with | - gnrc_indx:  {}  new_gnrc_indx:  {}".format(
                    name, gnrc_indx, new_gnrc_indx))
                new_list[i] = new_gnrc_indx

    new_metadata_df = metadata_df.copy()
    new_metadata_df.columns = results[0]
    new_metadata_df.index = results[1]

    return new_metadata_df
