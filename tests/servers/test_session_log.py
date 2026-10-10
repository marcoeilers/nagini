"""The session-log reader behind the whole-run timeout report (no JVM needed)."""

import os

from nagini_translation import session_log


LOG = """;; prover: z3 -smt2 -in
; ---------- CFG ----------
; ---------- PriorityTree_reprioritize ----------
(declare-const x Int)
; [check #0 start kind=saturate t=900]
(check-sat)
unknown
; [check #0 kind=saturate answer=unknown reason=(incomplete quantifiers) ms=9000 rlimit=1 budgetMs=50 t=900]
; [check #1 start kind=assert t=1000 at=candidate.py@57.8--57.40]
(check-sat)
unsat
; [check #1 kind=assert answer=unsat ms=12 rlimit=900 budgetMs=500 qi=3 t=1000 at=candidate.py@57.8--57.40]
; ---------- FUNCTION lemma_bound----------
; [check #2 start kind=check t=2000]
(check-sat)
unknown
; [check #2 kind=check answer=unknown reason=(incomplete (theory arithmetic)) ms=700 rlimit=4500000 budgetMs=500 qi=41000 t=2000]
; [check #3 start kind=assert t=3000 at=candidate.py@61.4--61.9]
(check-sat)
"""
BUILTIN = """; ---------- FUNCTION int___eq__----------
; [check #1 start kind=check t=100 at=bool.sil@324.13--324.60]
(check-sat)
unknown
; [check #1 kind=check answer=unknown reason=(incomplete quantifiers) ms=99999 budgetMs=10 t=100 at=bool.sil@324.13--324.60]
"""


def test_read_session_checks_and_in_flight(tmp_path):
    p = tmp_path / 'session-00-1.smt2'
    p.write_text(LOG)
    s = session_log.read_session(str(p))
    assert [c['ordinal'] for c in s['checks']] == [0, 1, 2]
    _, first, second = s['checks']
    assert first == {'ordinal': 1, 'kind': 'assert', 'answer': 'unsat', 'reason': None,
                     'ms': 12, 'budgetMs': 500, 'instantiations': 3, 'startedAt': 1000,
                     'at': 'candidate.py:57', 'member': 'PriorityTree_reprioritize'}
    assert second['reason'] == '(incomplete (theory arithmetic))'
    assert second['member'] == 'lemma_bound' and second['at'] is None
    assert s['inFlight'] == {'ordinal': 3, 'kind': 'assert', 'startedAt': 3000,
                             'at': 'candidate.py:61', 'member': 'lemma_bound'}


def test_timeout_report(tmp_path):
    (tmp_path / 'session-00-1.smt2').write_text(LOG)
    (tmp_path / 'session-01-2.smt2').write_text(BUILTIN)
    (tmp_path / 'smtstate-1-canceled-x.smt2').write_text(LOG)
    names = {'PriorityTree_reprioritize': 'PriorityTree.reprioritize'}
    r = session_log.timeout_report(str(tmp_path), now_ms=10000,
                                   member_name=lambda n: names.get(n, n), top=1)
    assert r['inFlight'] == [{'verifier': '00', 'member': 'lemma_bound', 'at': 'candidate.py:61',
                              'kind': 'assert', 'runningMs': 7000}]
    assert r['slowestChecks'] == [{'member': 'lemma_bound', 'at': None, 'kind': 'check',
                                   'answer': 'unknown', 'reason': '(incomplete (theory arithmetic))',
                                   'ms': 700, 'instantiations': 41000}]
    assert r['memberCheckTotals'] == {'lemma_bound': {'checks': 1, 'ms': 700}}


def test_timeout_report_without_sessions(tmp_path):
    assert session_log.timeout_report(str(tmp_path), now_ms=0) is None
    assert session_log.source_line('seq.sil@30.13--30.165') == 'seq.sil:30'
    assert session_log.source_line(None) is None
