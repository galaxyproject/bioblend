from collections.abc import Iterable
from typing import TypeVar

T = TypeVar("T")


def get_one(iterable: Iterable[T]) -> T:
    seq = list(iterable)
    assert len(seq) == 1
    return seq[0]
