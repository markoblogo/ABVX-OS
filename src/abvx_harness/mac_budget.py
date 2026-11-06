"""Cooperative monotonic budget shared by one observer and nested maintenance."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import time

_deadline = ContextVar('mac_observer_deadline', default=None)


class Expired(TimeoutError):
    """No further work may start; checkpoint and return without automatic retry."""


def remaining():
    deadline = _deadline.get()
    return None if deadline is None else max(0.0, deadline-time.monotonic())


def check(minimum=0.0):
    left = remaining()
    if left is not None and left <= minimum:
        raise Expired()


def timeout(seconds):
    check(0.1)
    left = remaining()
    return seconds if left is None else min(seconds, max(0.01, left-0.1))


@contextmanager
def limit(seconds):
    deadline = time.monotonic()+max(0, seconds)
    parent = _deadline.get()
    token = _deadline.set(min(parent, deadline) if parent is not None else deadline)
    try:
        yield
    finally:
        _deadline.reset(token)


def bounded(seconds):
    def decorate(fn):
        @wraps(fn)
        def run(*args, **kwargs):
            with limit(seconds):
                return fn(*args, **kwargs)
        return run
    return decorate
