import os
import logging
from blend.config import Config, BlendConfigLocations

# Current version of the library
__version__ = '0.12'

config = Config()


def init_logging():
    for file in BlendConfigLocations:
        try:
            logging.config.fileConfig(os.path.expanduser(file))
        except:
            pass


class NullHandler(logging.Handler):
    def emit(self, record):
        pass

# By default, do not force any logging by the library. If you want to see the
# log messages in your scripts, add the following to the top of your script:
#   import logging
#   logging.basicConfig(filename="blend.log", level=logging.DEBUG)

default_format_string = "%(asctime)s %(name)s [%(levelname)s]: %(message)s"
log = logging.getLogger('blend')
log.addHandler(NullHandler())
init_logging()

# Convenience functions to set logging to a particular file or stream
# To enable either of these, simply add the following at the top of a
# blend module:
#   import blend
#   blend.set_stream_logger(__name__)


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
