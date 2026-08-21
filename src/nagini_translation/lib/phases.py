"""Per-request phase timings (typecheck, translate, chop, verify).

Kept in a thread-local so concurrent service requests do not mix: each
request runs its whole translate-and-verify pipeline on one thread.
"""
import threading
import time
from contextlib import contextmanager
from typing import Dict, Optional

_local = threading.local()

ORDER = ('typecheck', 'translate', 'chop', 'verify')


def reset() -> None:
    _local.phases = {}


def record(name: str, seconds: float) -> None:
    phases = getattr(_local, 'phases', None)
    if phases is None:
        phases = _local.phases = {}
    phases[name] = phases.get(name, 0.0) + seconds


@contextmanager
def phase(name: str):
    start = time.time()
    try:
        yield
    finally:
        record(name, time.time() - start)


def phases() -> Dict[str, float]:
    phases = getattr(_local, 'phases', None) or {}
    return {k: round(phases[k], 2) for k in ORDER if k in phases}


def summary(timings: Optional[Dict[str, float]] = None) -> str:
    """``typecheck 4s, translate 18s, chop 190s, verify 360s``."""
    timings = phases() if timings is None else timings
    return ', '.join('%s %.0fs' % (k, timings[k]) for k in ORDER if k in timings)
