"""
gmt.py

IO methods for handling GMT files.

A GMT is stored as a list of dictionaries.
Each line is its own dictionary.
Each dictionary has the following keys:
    - head (string): identifier for the set
    - desc (string): longer description of the set
    - entry (list): members of the set

AUTHOR: Corey Flynn, Broad Institute, 2012
MODIFIED: Lev Litichevskiy, 2017

"""
import os

SET_IDENTIFIER_FIELD = "head"
SET_DESC_FIELD = "desc"
SET_MEMBERS_FIELD = "entry"


def read(file_path):
    """ Read a gmt file at the path specified by file_path.

    Each line of the file is expected to be tab-delimited with at least 3 fields: a set
    identifier, a set description, and one or more set members (any trailing empty fields,
    e.g. from extra trailing tabs, are dropped). Set identifiers must be unique across the
    file, and, within a single line, member entries must be unique.

    Args:
        file_path (string): path to gmt file

    Returns:
        gmt (GMT object): list of dicts, where each dict corresponds to one
            line of the GMT file, with keys "head" (set identifier), "desc"
            (set description), and "entry" (list of set members)

    Raises:
        AssertionError: if a line has fewer than 3 tab-delimited fields, if a line has
            duplicate entries, or if set identifiers are not unique across the file

    """
    # Read in file
    actual_file_path = os.path.expanduser(file_path)
    with open(actual_file_path, 'r') as f:
        lines = f.readlines()
    
    # Create GMT object
    gmt = []
    
    # Iterate over each line
    for line_num, line in enumerate(lines):
        # Separate along tabs
        fields = line.split('\t')

        assert len(fields) > 2, (
            "Each line must have at least 3 tab-delimited items. " +
            "line_num: {}, fields: {}").format(line_num, fields)
        
        # Get rid of trailing whitespace
        fields[-1] = fields[-1].rstrip()
        
        # Collect entries
        entries = fields[2:]
        
        # Remove empty entries
        entries = [x for x in entries if x]

        assert len(set(entries)) == len(entries), (
            "There should not be duplicate entries for the same set. " +
            "line_num: {}, entries: {}").format(line_num, entries)

        # Store this line as a dictionary
        line_dict = {SET_IDENTIFIER_FIELD: fields[0],
                     SET_DESC_FIELD: fields[1],
                     SET_MEMBERS_FIELD: entries}
        gmt.append(line_dict)

    verify_gmt_integrity(gmt)

    return gmt


def verify_gmt_integrity(gmt):
    """ Make sure that set ids are unique.

    Args:
        gmt (GMT object): list of dicts

    Returns:
        None

    Raises:
        AssertionError: if set identifiers (the "head" field) are not unique across gmt

    """

    # Verify that set ids are unique
    set_ids = [d[SET_IDENTIFIER_FIELD] for d in gmt]
    assert len(set(set_ids)) == len(set_ids), (
        "Set identifiers should be unique. set_ids: {}".format(set_ids))


def write(gmt, out_path):
    """ Write a GMT to a text file.

    Args:
        gmt (GMT object): list of dicts
        out_path (string): output path

    Returns:
        None

    """
    with open(out_path, 'w') as f:
        for _, each_dict in enumerate(gmt):
            f.write(each_dict[SET_IDENTIFIER_FIELD] + '\t')
            f.write(each_dict[SET_DESC_FIELD] + '\t')
            f.write('\t'.join([str(entry) for entry in each_dict[SET_MEMBERS_FIELD]]))
            f.write('\n')
