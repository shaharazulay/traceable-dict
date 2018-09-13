from contextlib import contextmanager

__all__ = []

_time = None


@contextmanager
def set_time(timestamp):
    time = _time
    _set_time(timestamp)
    try:
        yield
    finally:
        _set_time(time)


__all__ += ['set_time']


def _set_time(timestamp):
    global _time
    _time = timestamp


def get_time():
    if _time is None:
        raise ValueError("value for time cannot be None")
    return _time


__all__ += ['get_time']