def get_one(iterable):
    seq = list(iterable)
    assert len(seq) == 1
    return seq[0]
