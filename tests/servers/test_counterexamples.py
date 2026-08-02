"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""Service-level tests for structured counterexamples (Silicon backend)."""


_PURE_FAIL_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "@Pure\n"
    "def bad(a: int) -> int:\n"
    "    Requires(a >= 0)\n"
    "    Ensures(Result() > a)\n"
    "    return a\n"
)


def _write(tmp_path, name, src):
    p = tmp_path / name
    p.write_text(src)
    return str(p)


def test_counterexample_structured_model(service, fail_file):
    result = service.verify(fail_file, counterexample=True)
    assert not result.success
    assert result.diagnostics
    ce = result.diagnostics[0].counterexample
    assert ce is not None
    assert ce['kind'] == 'model'
    # The failing method's arguments appear in the old store.
    old_names = {e['name'] for e in ce['oldStore']}
    assert {'a', 'b'} <= old_names
    # The current store contains the result.
    store_names = {e['name'] for e in ce['store']}
    assert 'Result()' in store_names
    # The whole result must serialize to JSON (what the server sends).
    import json
    json.dumps(result.to_dict())


def test_counterexample_pure_method_has_no_old_state(service, tmp_path):
    path = _write(tmp_path, "pure_fail.py", _PURE_FAIL_SRC)
    result = service.verify(path, counterexample=True)
    assert not result.success
    assert result.diagnostics
    ce = result.diagnostics[0].counterexample
    assert ce is not None
    assert ce['kind'] == 'model'
    assert ce['oldStore'] is None
    assert ce['oldHeap'] is None
    store_names = {e['name'] for e in ce['store']}
    assert 'a' in store_names


def test_no_counterexample_when_not_requested(service, fail_file):
    result = service.verify(fail_file, counterexample=False)
    assert not result.success
    assert result.diagnostics
    assert result.diagnostics[0].counterexample is None


def test_verify_structured_single_shot(service, fail_file):
    # verify_structured reuses an existing JVM; borrow the service's one.
    from nagini_translation.service import verify_structured
    result = verify_structured(service.jvm, fail_file, counterexample=True)
    assert not result.success
    assert result.diagnostics
    ce = result.diagnostics[0].counterexample
    assert ce is not None and ce['kind'] == 'model'
