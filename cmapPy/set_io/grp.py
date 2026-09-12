"""
grp.py

IO methods for handling GRP files.

A GRP file is stored as a list. Lines beginning with # are ignored.

AUTHOR: David Wadden, Broad Institute, 2012
MODIFIED: Lev Litichevskiy, 2017
"""

import os
import re


def read(in_path):
    """ Read a grp file at the path specified by in_path.

    Lines beginning with "#" are treated as comments and skipped. Every other line has
    leading/trailing whitespace stripped and is kept as an entry, including blank lines
    (which become empty strings in the returned list).

    Args:
        in_path (string): path to GRP file

    Returns:
        grp (list): list of strings, one per non-comment line of the file

    Raises:
        AssertionError: if in_path does not exist

    """
    assert os.path.exists(in_path), "The following GRP file can't be found. in_path: {}".format(in_path)

    with open(in_path, "r") as f:
        lines = f.readlines()
        # need the second conditional to ignore comment lines
        grp = [line.strip() for line in lines if line and not re.match("^#", line)]

    return grp


def write(grp, out_path):
    """ Write a GRP to a text file.

    Args:
        grp (list): GRP object to write to new-line delimited text file
        out_path (string): output path

    Returns:
        None

    """
    with open(out_path, "w") as f:
        for x in grp:
            f.write(str(x) + "\n")