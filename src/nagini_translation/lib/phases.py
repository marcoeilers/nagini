"""Per-request phase timings (ORDER): the pipeline's phases, the parts of
typecheck (``typecheck.*``, contained in it) and the waits between them
(``lock``: for the service's translation lock, ``queued``: for the backend).

Kept in a thread-local so concurrent service requests do not mix: each
request runs its whole translate-and-verify pipeline on one thread.
"""
import threading
import time
from contextlib import contextmanager
from typing import Dict, Optional

_local = threading.local()

TYPECHECK_PARTS = ('typecheck.evict', 'typecheck.strict', 'typecheck.nonstrict',
                   'typecheck.visit')
ORDER = ('lock', 'typecheck', *TYPECHECK_PARTS, 'translate', 'erase', 'chop',
         'queued', 'verify')
# in a recorded attempt's meta, not in a result
RECORDED_ONLY = ('lock', *TYPECHECK_PARTS, 'erase', 'queued')


def reset() -> None:
    _local.phases = {}
    _local.cpu = {}


def record(name: str, seconds: float, cpu: float = None) -> None:
    """Adds ``seconds`` of wall time to the phase and, if given, ``cpu``
    seconds the request's thread ran during them."""
    if getattr(_local, 'phases', None) is None:
        reset()
    _local.phases[name] = _local.phases.get(name, 0.0) + seconds
    if cpu is not None:
        _local.cpu[name] = _local.cpu.get(name, 0.0) + cpu


@contextmanager
def phase(name: str):
    start, cpu_start = time.time(), time.thread_time()
    try:
        yield
    finally:
        record(name, time.time() - start, time.thread_time() - cpu_start)


def _ordered(values: Dict[str, float]) -> Dict[str, float]:
    return {k: round(values[k], 2) for k in ORDER if k in values}


def phases() -> Dict[str, float]:
    return _ordered(getattr(_local, 'phases', None) or {})


def cpu() -> Dict[str, float]:
    """Per phase, the seconds the request's thread ran: the rest of the
    phase's wall time it waited (for the interpreter lock, I/O, a core, or
    work done on other threads)."""
    return _ordered(getattr(_local, 'cpu', None) or {})


def reported(timings: Dict[str, float]) -> Dict[str, float]:
    """``timings`` as a result shows them."""
    return {k: v for k, v in timings.items() if k not in RECORDED_ONLY}


def summary(timings: Optional[Dict[str, float]] = None) -> str:
    """``typecheck 4s, translate 18s, chop 190s, verify 360s``."""
    timings = reported(phases() if timings is None else timings)
    return ', '.join('%s %.0fs' % (k, timings[k]) for k in ORDER if k in timings)
