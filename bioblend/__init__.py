import logging
import os

from bioblend.config import (
    BioBlendConfigLocations,
    Config,
)

# Current version of the library
__version__ = '0.16.0'

# default chunk size (in bytes) for reading remote data
try:
    import resource
    CHUNK_SIZE = resource.getpagesize()
except Exception:
    CHUNK_SIZE = 4096


config = Config()


def get_version():
    """
    Returns a string with the current version of the library (e.g., "0.2.0")
    """
    return __version__


def init_logging():
    """
    Initialize BioBlend's logging from a configuration file.
    """
    for config_file in BioBlendConfigLocations:
        try:
            logging.config.fileConfig(os.path.expanduser(config_file))
        except Exception:
            pass


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


# By default, do not force any logging by the library. If you want to see the
# log messages in your scripts, add the following to the top of your script:
#   import logging
#   logging.basicConfig(filename="bioblend.log", level=logging.DEBUG)
default_format_string = "%(asctime)s %(name)s [%(levelname)s]: %(message)s"
log = logging.getLogger('bioblend')
log.addHandler(NullHandler())
init_logging()

# Convenience functions to set logging to a particular file or stream
# To enable either of these, simply add the following at the top of a
# bioblend module:
#   import bioblend
#   bioblend.set_stream_logger(__name__)


def set_file_logger(name, filepath, level=logging.INFO, format_string=None):
    global log
    if not format_string:
        format_string = default_format_string
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fh = logging.FileHandler(filepath)
    fh.setLevel(level)
    formatter = logging.Formatter(format_string)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    log = logger


def set_stream_logger(name, level=logging.DEBUG, format_string=None):
    global log
    if not format_string:
        format_string = default_format_string
    logger = logging.getLogger(name)
    logger.setLevel(level)
    fh = logging.StreamHandler()
    fh.setLevel(level)
    formatter = logging.Formatter(format_string)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    log = logger


class ConnectionError(Exception):
    """
    An exception class that is raised when unexpected HTTP responses come back.

    Should make it easier to debug when strange HTTP things happen such as a
    proxy server getting in the way of the request etc.
    @see: body attribute to see the content of the http response
    """
    def __init__(self, message, body=None, status_code=None):
        super().__init__(message)
        self.body = body
        self.status_code = status_code

    def __str__(self):
        return f"{self.args[0]}: {self.body}"


class TimeoutException(Exception):
    pass
