"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""


"""Shared fixtures for the LSP/MCP server tests.

These are integration tests: they start one in-process Nagini verification
service (JVM + ViperServer) for the whole session and reuse it. If the service
cannot be started (e.g. Viper jars or Z3 are unavailable), the tests are
skipped rather than failed. Run them with::

    pytest tests/servers
"""


import pytest


PASS_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def add(a: int, b: int) -> int:\n"
    "    Requires(a >= 0 and b >= 0)\n"
    "    Ensures(Result() >= a)\n"
    "    return a + b\n"
)

FAIL_SRC = (
    "from nagini_contracts.contracts import *\n\n"
    "def add(a: int, b: int) -> int:\n"
    "    Requires(a >= 0 and b >= 0)\n"
    "    Ensures(Result() > a)\n"
    "    return a + b\n"
)


@pytest.fixture(scope="session")
def service():
    try:
        from nagini_translation.service import VerificationService
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip("Nagini service could not be imported: {}".format(e))
    try:
        svc = VerificationService()
    except Exception as e:  # pragma: no cover - environment dependent
        pytest.skip("Nagini verification service unavailable: {}".format(e))
    yield svc
    try:
        svc.shutdown()
    except Exception:
        pass


@pytest.fixture
def pass_src():
    return PASS_SRC


@pytest.fixture
def fail_src():
    return FAIL_SRC


@pytest.fixture
def pass_file(tmp_path):
    p = tmp_path / "pass_example.py"
    p.write_text(PASS_SRC)
    return str(p)


@pytest.fixture
def fail_file(tmp_path):
    p = tmp_path / "fail_example.py"
    p.write_text(FAIL_SRC)
    return str(p)
