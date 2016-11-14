import os
from collections import namedtuple


class Bunch(object):
    """
    A convenience class to allow dict keys to be represented as object fields.

    The end result is that this allows a dict to be to be represented the same
    as a database class, thus the two become interchangeable as a data source.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        """
        Return the contents of the dict in a printable representation
        """
        return str(self.__dict__)


def _file_stream_close(self):
    """
    Close the open file descriptor associated with the FileStream
    object.
    """
    self[1].close()


FileStream = namedtuple("FileStream", ["name", "fd"])
FileStream.close = _file_stream_close


def attach_file(path, name=None):
    """
    Attach a path to a request payload object.

    :type path: str
    :param path: Path to file to attach to payload.

    :type name: str
    :param name: Name to give file, if different than actual pathname.

    :rtype: object
    :return: Returns an object compatible with requests post operation and
             capable of being closed with a ``close()`` method.
    """
    if name is None:
        name = os.path.basename(path)
    attachment = FileStream(name, open(path, "rb"))
    return attachment


__all__ = (
    'Bunch',
    'attach_file',
)
