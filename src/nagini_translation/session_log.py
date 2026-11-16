"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""
The prover session logs Silicon leaves in its SMT state dir (one per
verifier): a member header per verified member, a line before every check-sat
and a summary line after it. Read when a run times out, to say what each
verifier was doing and where the time went.
"""


import os
import re

from typing import Callable, List, Optional


_MEMBER = re.compile(r'^; -{10} (?:FUNCTION )?(\S+?) ?-{10}$')
_START = re.compile(r'^; \[check #(\d+) start kind=(\w+) t=(\d+)(?: at=(\S+))?\]$')
_SUMMARY = re.compile(r'^; \[check #(\d+) kind=(\w+) answer=(\S+)(?: reason=(.*?))? ms=(\d+)'
                      r'(?: rlimit=(\d+))? budgetMs=(\d+)(?: qi=(\d+))? t=(\d+)(?: at=(\S+))?\]$')
_POSITION = re.compile(r'^(.*)@(\d+)\.(\d+)')
_SESSION_FILE = re.compile(r'^session-(\w+)-.*\.smt2$')
_BUILTIN = re.compile(r'\.sil:\d+$')  # a position in a Viper library file: a builtin's


def source_line(at: Optional[str]) -> Optional[str]:
    """``file:line`` from a Viper source position string (``file@l.c--l.c``)."""
    if not at:
        return None
    m = _POSITION.match(at)
    return '%s:%s' % (m.group(1), m.group(2)) if m else at


def read_session(path: str) -> dict:
    """The completed checks of one session log and the check it ends in, if any:
    ``{'checks': [...], 'inFlight': {...} | None}``, each check with its
    ``member`` (the header it fell under) and ``at`` as ``file:line``."""
    member = None
    checks: List[dict] = []
    started = None
    with open(path, errors='replace') as f:
        for line in f:
            line = line.rstrip('\n')
            m = _MEMBER.match(line)
            if m:
                if m.group(1) != 'CFG':
                    member = m.group(1)
                continue
            m = _START.match(line)
            if m:
                started = {'ordinal': int(m.group(1)), 'kind': m.group(2),
                           'startedAt': int(m.group(3)), 'at': source_line(m.group(4)),
                           'member': member}
                continue
            m = _SUMMARY.match(line)
            if m:
                started = None
                checks.append({
                    'ordinal': int(m.group(1)), 'kind': m.group(2), 'answer': m.group(3),
                    'reason': m.group(4), 'ms': int(m.group(5)),
                    'budgetMs': int(m.group(7)),
                    'instantiations': int(m.group(8)) if m.group(8) else None,
                    'startedAt': int(m.group(9)), 'at': source_line(m.group(10)),
                    'member': member})
    return {'checks': checks, 'inFlight': started}


def timeout_report(smtstate_dir: str, now_ms: int,
                   member_name: Callable[[str], str] = lambda n: n,
                   top: int = 10) -> Optional[dict]:
    """What the verifiers were doing when the run ended, from every session log
    in ``smtstate_dir``: the in-flight checks with how long they had been
    running, the ``top`` slowest completed checks, and the check count and
    time of the ``top`` members with the most time. Saturation checks (the
    backend's prover warm-ups) and the builtins' checks are left out of the
    slowest and the totals. ``member_name`` maps a Viper member name to the
    front end's; None when there are no session logs."""
    sessions = {}
    for name in sorted(os.listdir(smtstate_dir)):
        m = _SESSION_FILE.match(name)
        if m:
            sessions[m.group(1)] = read_session(os.path.join(smtstate_dir, name))
    if not sessions:
        return None

    def check_view(c: dict, keys) -> dict:
        view = {k: c[k] for k in keys}
        view['member'] = member_name(c['member']) if c['member'] else None
        return view

    in_flight = []
    for verifier, session in sessions.items():
        c = session['inFlight']
        if c is not None:
            in_flight.append({'verifier': verifier,
                              **check_view(c, ('member', 'at', 'kind')),
                              'runningMs': max(0, now_ms - c['startedAt'])})
    checks = [c for s in sessions.values() for c in s['checks']
              if c['kind'] != 'saturate' and not (c['at'] and _BUILTIN.search(c['at']))]
    slowest = [check_view(c, ('member', 'at', 'kind', 'answer', 'reason', 'ms', 'instantiations'))
               for c in sorted(checks, key=lambda c: -c['ms'])[:top]]
    totals: dict = {}
    for c in checks:
        t = totals.setdefault(member_name(c['member']) if c['member'] else '?',
                              {'checks': 0, 'ms': 0})
        t['checks'] += 1
        t['ms'] += c['ms']
    totals = dict(sorted(totals.items(), key=lambda kv: -kv[1]['ms'])[:top])
    return {'inFlight': in_flight, 'slowestChecks': slowest, 'memberCheckTotals': totals}
