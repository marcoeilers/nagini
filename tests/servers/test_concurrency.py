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
