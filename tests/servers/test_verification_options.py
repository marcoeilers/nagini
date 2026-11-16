"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""Service-level tests for verification options: --ignore-global,
--disable-branch-conditions, obligation auto-detection, per-request Viper
backend arguments, and include_viper."""

import threading
import time


_TOPLEVEL_ASSERT_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "assert False\n"
)

_BRANCH_ERROR_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def f(x: int) -> None:\n"
    "    if x > 0:\n"
    "        assert False\n"
)

_NO_OBLIGATIONS_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def f(a: int) -> int:\n"
    "    Requires(a >= 0)\n"
    "    Ensures(Result() >= a)\n"
    "    return a\n"
)

_MUST_TERMINATE_OK_SRC = (
    "from nagini_contracts.contracts import *\n"
    "from nagini_contracts.obligations import MustTerminate\n\n"
    "def f(n: int) -> int:\n"
    "    Requires(MustTerminate(1))\n"
    "    return n\n"
)

_MUST_TERMINATE_BAD_SRC = (
    "from nagini_contracts.contracts import *\n"
    "from nagini_contracts.obligations import MustTerminate\n\n"
    "def rec(n: int) -> int:\n"
    "    Requires(MustTerminate(1))\n"
    "    return rec(n)\n"
)


_SLOW_THEN_FAILING_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def slow(a: int, b: int, c: int, d: int) -> None:\n"
    "    Requires(a > 1 and b > 1 and c > 1 and d > 1)\n"
    + "".join("    Assert(a * b * c * d + {0} > a * b + {0})\n".format(i) for i in range(150))
    + "    Assert(a > 1000)\n"
)

_QUICK_FAILING_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def quick(x: int) -> None:\n"
    "    Assert(x > 0)\n"
)


def _write(tmp_path, name, src):
    p = tmp_path / name
    p.write_text(src)
    return str(p)


# -- --ignore-global --------------------------------------------------------

def test_ignore_global_toggles_toplevel_verification(service, tmp_path):
    without = _write(tmp_path, "toplevel_a.py", _TOPLEVEL_ASSERT_SRC)
    with_ignore = _write(tmp_path, "toplevel_b.py", _TOPLEVEL_ASSERT_SRC)
    # By default the top-level statements are verified, so the false assert fails.
    result = service.verify(without)
    assert not result.success
    assert any(d.code == "assert.failed:assertion.false" for d in result.diagnostics)
    # With ignore_global, top-level statements are skipped, so it verifies.
    assert service.verify(with_ignore, ignore_global=True).success


# -- --disable-branch-conditions --------------------------------------------

def test_disable_branch_conditions_reported_then_suppressed(service, tmp_path):
    original = service.current_options()
    try:
        service.reconfigure(disable_branch_conditions=False)
        on = service.verify(_write(tmp_path, "bc_on.py", _BRANCH_ERROR_SRC))
        assert not on.success
        # The failing assert is under `if x > 0`, so the branch condition is
        # reported.
        assert any(d.branch_conditions for d in on.diagnostics)

        service.reconfigure(disable_branch_conditions=True)
        off = service.verify(_write(tmp_path, "bc_off.py", _BRANCH_ERROR_SRC))
        assert not off.success
        assert all(not d.branch_conditions for d in off.diagnostics)
    finally:
        service.reconfigure(
            disable_branch_conditions=original["disableBranchConditions"])


# -- obligation auto-detection ----------------------------------------------

def test_obligations_autodetected_per_program(service, tmp_path):
    # A program without obligations: the encoding is auto-detected as
    # unnecessary and it verifies.
    assert service.verify(
        _write(tmp_path, "no_obligations.py", _NO_OBLIGATIONS_SRC)).success

    # A program with a satisfiable MustTerminate obligation: the encoding must be
    # (re-)enabled -- not left disabled from the previous no-obligation program
    # -- and it verifies.
    assert service.verify(
        _write(tmp_path, "must_terminate_ok.py", _MUST_TERMINATE_OK_SRC)).success

    # A MustTerminate obligation that cannot hold (non-terminating recursion)
    # must fail -- which it can only detect if the obligation encoding is active.
    bad = service.verify(
        _write(tmp_path, "must_terminate_bad.py", _MUST_TERMINATE_BAD_SRC))
    assert not bad.success
    assert bad.diagnostics


# -- per-request viper args ---------------------------------------------------

def test_viper_args_reach_the_backend_command_line(service, tmp_path):
    original = service.current_options()
    try:
        service.reconfigure(disable_branch_conditions=True)
        # Baseline: the service-wide option suppresses branch conditions.
        off = service.verify(_write(tmp_path, "va_off.py", _BRANCH_ERROR_SRC))
        assert not off.success
        assert all(not d.branch_conditions for d in off.diagnostics)
        # Re-enabling the flag through per-request viper_args overrides it,
        # which proves the arguments end up on the backend command line.
        on = service.verify(
            _write(tmp_path, "va_on.py", _BRANCH_ERROR_SRC),
            viper_args=["--enableBranchconditionReporting"])
        assert not on.success
        assert any(d.branch_conditions for d in on.diagnostics)
    finally:
        service.reconfigure(
            disable_branch_conditions=original["disableBranchConditions"])


def test_viper_args_invalid_option_fails_cleanly(service, tmp_path):
    result = service.verify(
        _write(tmp_path, "va_bad.py", _NO_OBLIGATIONS_SRC),
        viper_args=["--no-such-silicon-option"])
    assert not result.success


def test_prover_out_of_memory_reported_as_timeout(service, tmp_path):
    path = _write(tmp_path, "oom.py", _NO_OBLIGATIONS_SRC)
    capped = ["--proverConfigArgs=memory_max_size=1", "--disableCaching"]
    result = service.verify(path, viper_args=capped)
    assert not (result.success or result.crashed)
    [diag] = result.diagnostics
    assert diag.code == "TimeoutOccurred"
    assert "memory limit of 1 MB" in diag.message
    # Plain diagnostics keep the backend's crash.
    service.plain_diagnostics = True
    try:
        plain = service.verify(path, viper_args=capped)
    finally:
        service.plain_diagnostics = False
    assert plain.crashed
    assert plain.diagnostics[0].code == "verifier.crashed"


def test_concurrent_requests_keep_their_own_backend_options(service, tmp_path):
    # Silicon's configuration is process-global: a job started next to one with
    # other options would change that job's per-check budget mid-run.
    slow = _write(tmp_path, "gate_slow.py", _SLOW_THEN_FAILING_SRC)
    quick = _write(tmp_path, "gate_quick.py", _QUICK_FAILING_SRC)
    results = {}

    def run(path, budget):
        results[path] = service.verify(path, viper_args=[
            "--assertTimeout=%d" % budget, "--smtStateOnError", "--disableCaching"])

    first = threading.Thread(target=run, args=(slow, 5000))
    first.start()
    time.sleep(3)  # the slow job is verifying when the quick one arrives
    run(quick, 500)
    first.join()
    budgets = lambda r: [d.debug["failingCheck"]["budgetMs"] for d in r.diagnostics]
    assert budgets(results[slow]) == [5000]
    assert budgets(results[quick]) == [500]


# -- include_viper ------------------------------------------------------------

def test_include_viper_returns_translated_program(service, tmp_path):
    result = service.verify(_write(tmp_path, "iv.py", _NO_OBLIGATIONS_SRC),
                            include_viper=True)
    assert result.success
    assert "method" in result.viper_program
    # Off by default, and then absent from the serialized result.
    default = service.verify(_write(tmp_path, "iv2.py", _NO_OBLIGATIONS_SRC))
    assert default.viper_program is None
    assert "viperProgram" not in default.to_dict()
