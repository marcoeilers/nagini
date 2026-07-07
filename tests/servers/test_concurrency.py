"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""Concurrency and precise-cancellation tests for the verification service.

These use a Z3-heavier real example (``cav_example.py``) so that verifications
take long enough to genuinely overlap and to leave a window for cancelling one
job while the others keep running.
"""


import os
import threading
import time

import pytest


_EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "functional",
                        "verification", "examples", "cav_example.py")


@pytest.fixture
def heavy_copies(tmp_path):
    if not os.path.exists(_EXAMPLE):
        pytest.skip("cav_example.py not available")
    with open(_EXAMPLE) as f:
        src = f.read()
    paths = []
    for i in range(3):
        p = tmp_path / "heavy_{}.py".format(i)
        p.write_text(src)
        paths.append(str(p))
    return paths


@pytest.fixture
def concurrent_service(service):
    # The job-token machinery only applies on the ViperServer concurrent path.
    if not service._can_run_concurrently(arp=False):
        pytest.skip("ViperServer concurrent path not available")
    return service


def _wait_until_in_flight(service, tokens, timeout=180):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with service._jobs_lock:
            current = set(service._jobs)
        if set(tokens) <= current:
            return True
        time.sleep(0.05)
    return False


def test_two_jobs_run_concurrently_and_both_succeed(concurrent_service,
                                                    heavy_copies):
    results = {}

    def run(i, token):
        results[token] = concurrent_service.verify(heavy_copies[i],
                                                   job_token=token)

    threads = [threading.Thread(target=run, args=(0, "a")),
               threading.Thread(target=run, args=(1, "b"))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=180)

    assert all(not t.is_alive() for t in threads)
    assert results["a"].success and not results["a"].diagnostics
    assert results["b"].success and not results["b"].diagnostics


# Distinct failing functions appended to the heavy (correct) cav_example body,
# so the two surviving jobs are different programs with *different* errors that
# also take long enough to genuinely overlap.
_POSTCONDITION_SUFFIX = (
    "\n\ndef nagini_concurrency_bad_postcondition(a: int) -> int:\n"
    "    Ensures(Result() > a)\n"
    "    return a\n"
)
_ASSERT_SUFFIX = (
    "\n\ndef nagini_concurrency_bad_assert() -> None:\n"
    "    assert False\n"
)


@pytest.fixture
def erroring_programs(tmp_path):
    if not os.path.exists(_EXAMPLE):
        pytest.skip("cav_example.py not available")
    with open(_EXAMPLE) as f:
        cav = f.read()
    post = tmp_path / "prog_postcondition.py"
    post.write_text(cav + _POSTCONDITION_SUFFIX)
    middle = tmp_path / "prog_middle.py"
    middle.write_text(cav)
    asrt = tmp_path / "prog_assert.py"
    asrt.write_text(cav + _ASSERT_SUFFIX)
    return {"post": str(post), "mid": str(middle), "assert": str(asrt)}


def test_three_jobs_cancel_middle_distinct_errors_backtranslate(
        concurrent_service, erroring_programs):
    # Three concurrent jobs: two different failing programs and a heavy correct
    # one in the middle that we cancel. This checks that error back-translation
    # stays correct under concurrency (each job's errors map to its own source,
    # with no cross-contamination between the in-flight jobs).
    results = {}

    def run(token):
        results[token] = concurrent_service.verify(erroring_programs[token],
                                                   job_token=token)

    threads = [threading.Thread(target=run, args=(tok,))
               for tok in ("post", "mid", "assert")]
    for t in threads:
        t.start()

    # Cancel the middle job once it is in flight; the other two keep verifying.
    assert _wait_until_in_flight(concurrent_service, ["mid"]), \
        "middle job did not start in time"
    concurrent_service.cancel(job_token="mid")

    for t in threads:
        t.join(timeout=240)
    assert all(not t.is_alive() for t in threads), "a verification did not finish"

    POSTCONDITION = "postcondition.violated:assertion.false"
    ASSERT_FAILED = "assert.failed:assertion.false"

    # The middle job was cancelled, not verified.
    assert results["mid"].cancelled is True

    # Each survivor failed with its own, distinct, correctly back-translated
    # error...
    post_codes = {d.code for d in results["post"].diagnostics}
    assert_codes = {d.code for d in results["assert"].diagnostics}
    assert not results["post"].success and not results["assert"].success
    assert POSTCONDITION in post_codes
    assert ASSERT_FAILED in assert_codes
    # ...and did not pick up the other job's error (no cross-contamination).
    assert ASSERT_FAILED not in post_codes
    assert POSTCONDITION not in assert_codes
    # The reported error positions point into the respective files.
    assert any(d.file.endswith("prog_postcondition.py")
               for d in results["post"].diagnostics)
    assert any(d.file.endswith("prog_assert.py")
               for d in results["assert"].diagnostics)


# -- reconfiguration (including reload-triggering options) -------------------

_ASSERT_FAIL_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def check(x: int) -> None:\n"
    "    assert x > 0\n"
)

POSTCONDITION = "postcondition.violated:assertion.false"
ASSERT_FAILED = "assert.failed:assertion.false"


def test_reconfigure_int_bitops_reloads_and_still_verifies(service, pass_file,
                                                           fail_file):
    original = service.current_options()
    try:
        effective = service.reconfigure(int_bitops_size=16)
        assert effective["intBitopsSize"] == 16
        # The Silver resources were reloaded; verification still works correctly.
        assert service.verify(pass_file).success
        assert not service.verify(fail_file).success
    finally:
        service.reconfigure(int_bitops_size=original["intBitopsSize"])
    assert service.current_options()["intBitopsSize"] == original["intBitopsSize"]


def test_reconfigure_float_encoding_reloads_both_modes(service, pass_file):
    original = service.current_options()
    try:
        for encoding in ("ieee32", "real"):
            effective = service.reconfigure(float_encoding=encoding)
            assert effective["floatEncoding"] == encoding
            # Resources reloaded with the new float encoding; still functional.
            assert service.verify(pass_file).success
    finally:
        service.reconfigure(float_encoding=original["floatEncoding"])
    assert service.current_options()["floatEncoding"] == original["floatEncoding"]


# `Low(e)` is a no-op (translated to `true`) without SIF, but under SIF it
# asserts that `e` is non-secret. Asserting that an unconstrained parameter is
# Low therefore succeeds with SIF off and fails with SIF on.
_LOW_LEAK_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def leak(secret: int) -> None:\n"
    "    Assert(Low(secret))\n"
)


def test_reconfigure_sif_changes_low_semantics(service, tmp_path):
    # Verify the SAME program before, after, and in between toggling SIF, and
    # check the outcome flips: reconfigure(sif=...) changes verification
    # *semantics* (not just that the Silver resources reload).
    prog = tmp_path / "low_leak.py"
    prog.write_text(_LOW_LEAK_SRC)
    prog = str(prog)
    original = service.current_options()
    try:
        # SIF off: Low(secret) is trivially true -> verifies.
        assert service.verify(prog).success

        # SIF on: asserting that a secret is Low must fail.
        service.reconfigure(sif=True)
        sif_result = service.verify(prog)
        assert not sif_result.success
        assert any(d.code == "assert.failed:assertion.false"
                   for d in sif_result.diagnostics)

        # SIF off again: verifies once more.
        service.reconfigure(sif=False)
        assert service.verify(prog).success
    finally:
        service.reconfigure(sif=original["sif"])


def test_reconfigure_during_concurrent_verification_backtranslates(
        concurrent_service, erroring_programs):
    # Reconfigure (with a resources reload) *while* several jobs are in flight,
    # and check that those already-submitted jobs still back-translate their own
    # errors correctly.
    original = concurrent_service.current_options()
    results = {}

    def run(token):
        results[token] = concurrent_service.verify(erroring_programs[token],
                                                   job_token=token)

    threads = [threading.Thread(target=run, args=(tok,))
               for tok in ("post", "mid", "assert")]
    for t in threads:
        t.start()
    try:
        assert _wait_until_in_flight(concurrent_service,
                                     ["post", "mid", "assert"]), \
            "jobs did not all start in time"
        # Reload-triggering change mid-flight.
        assert concurrent_service.reconfigure(int_bitops_size=16)["intBitopsSize"] == 16
        for t in threads:
            t.join(timeout=240)
    finally:
        concurrent_service.reconfigure(int_bitops_size=original["intBitopsSize"])

    assert all(not t.is_alive() for t in threads), "a verification did not finish"
    post_codes = {d.code for d in results["post"].diagnostics}
    assert_codes = {d.code for d in results["assert"].diagnostics}
    assert results["mid"].success and not results["mid"].diagnostics
    assert POSTCONDITION in post_codes and ASSERT_FAILED not in post_codes
    assert ASSERT_FAILED in assert_codes and POSTCONDITION not in assert_codes


_PASS_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def add(a: int, b: int) -> int:\n"
    "    Requires(a >= 0 and b >= 0)\n"
    "    Ensures(Result() >= a)\n"
    "    return a + b\n"
)
_POST_FAIL_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def add(a: int, b: int) -> int:\n"
    "    Requires(a >= 0 and b >= 0)\n"
    "    Ensures(Result() > a)\n"
    "    return a + b\n"
)
_ASSERT_FAIL_SRC2 = (
    "from nagini_contracts.contracts import *\n\n"
    "def check() -> None:\n"
    "    assert False\n"
)


def test_config_changes_interleaved_with_concurrent_batches(concurrent_service,
                                                            tmp_path):
    # Run several concurrent batches with different config changes in between,
    # and check every job in every batch gets the correct, distinct result.
    files = {"ok": tmp_path / "ok.py", "post": tmp_path / "post.py",
             "asrt": tmp_path / "asrt.py"}
    files["ok"].write_text(_PASS_SRC)
    files["post"].write_text(_POST_FAIL_SRC)
    files["asrt"].write_text(_ASSERT_FAIL_SRC2)
    files = {k: str(v) for k, v in files.items()}

    def run_batch(tag):
        results = {}

        def run(token):
            results[token] = concurrent_service.verify(
                files[token], job_token="{}-{}".format(token, tag))

        threads = [threading.Thread(target=run, args=(tok,)) for tok in files]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=180)
        assert all(not t.is_alive() for t in threads)
        return results

    def check(results):
        assert results["ok"].success and not results["ok"].diagnostics
        assert any(d.code == POSTCONDITION for d in results["post"].diagnostics)
        assert any(d.code == ASSERT_FAILED for d in results["asrt"].diagnostics)

    original = concurrent_service.current_options()
    changes = [None, {"int_bitops_size": 16}, {"float_encoding": "ieee32"}]
    try:
        for i, change in enumerate(changes):
            if change is not None:
                concurrent_service.reconfigure(**change)
            check(run_batch(i))
    finally:
        concurrent_service.reconfigure(
            int_bitops_size=original["intBitopsSize"],
            float_encoding=original["floatEncoding"])
