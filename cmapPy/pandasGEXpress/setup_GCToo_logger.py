import logging
import logging.handlers


__author__ = "David Lahr"
__email__ = "dlahr@broadinstitute.org"

LOGGER_NAME = "cmap_logger"

_LOG_FORMAT = "%(levelname)s %(asctime)s %(module)s %(funcName)s %(message)s"
_LOG_FILE_MAX_BYTES = 10000000
_LOG_FILE_BACKUP_COUNT = 5


def setup(verbose=False, log_file=None):
    """ Configure the shared "cmap_logger" logger used throughout cmapPy.

    If log_file is None, configures the root logger via
    logging.basicConfig with the module's standard format (this affects
    logging output process-wide, since basicConfig configures the root
    logger). If log_file is given, instead attaches a RotatingFileHandler
    (max size _LOG_FILE_MAX_BYTES, keeping _LOG_FILE_BACKUP_COUNT backups)
    writing to log_file, using the same format, to the "cmap_logger" logger
    specifically.

    Input:
        Optional:
        - verbose (bool): if True, sets the logging level to DEBUG;
            otherwise INFO. Default = False.
        - log_file (str): path to a file to log to. If None, logs are sent
            to the console via logging.basicConfig instead. Default = None.

    Output:
        None (configures logging as a side effect)
    """
    logger = logging.getLogger(LOGGER_NAME)

    level = (logging.DEBUG if verbose else logging.INFO)

    if log_file is None:
        logging.basicConfig(level=level, format=_LOG_FORMAT)
    else:
        logger.setLevel(level)
        handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=_LOG_FILE_MAX_BYTES,
                                                       backupCount=_LOG_FILE_BACKUP_COUNT)
        handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT))
        logger.addHandler(handler)
