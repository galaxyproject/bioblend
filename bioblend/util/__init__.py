import os
from typing import (
    Any,
    IO,
    NamedTuple,
    Type,
    TypeVar,
)


class Bunch:
    """
    A convenience class to allow dict keys to be represented as object fields.

    The end result is that this allows a dict to be to be represented the same
    as a database class, thus the two become interchangeable as a data source.
    """

    def __init__(self, **kwargs: Any) -> None:
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        """
        Return the contents of the dict in a printable representation
        """
        return str(self.__dict__)


class FileStream(NamedTuple):
    name: str
    fd: IO

    def close(self) -> None:
        self.fd.close()


def attach_file(path: str, name: str = None) -> FileStream:
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
    return FileStream(name, open(path, "rb"))


T = TypeVar("T")


def abstractclass(decorated_cls: Type[T]) -> Type[T]:
    """
    Decorator that marks a class as abstract even without any abstract method

    Adapted from https://stackoverflow.com/a/49013561/4503125
    """

    def clsnew(cls: Type[T], *args: Any, **kwargs: Any) -> T:
        # assert issubclass(cls, decorated_cls)
        if cls is decorated_cls:
            cls_name = getattr(decorated_cls, "__name__", str(decorated_cls))
            raise TypeError(f"Can't instantiate abstract class {cls_name}")
        return super(decorated_cls, cls).__new__(cls)  # type: ignore[misc]

    decorated_cls.__new__ = clsnew  # type: ignore[assignment]
    return decorated_cls


__all__ = (
    "Bunch",
    "attach_file",
)
