# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def index(s: str) -> None:
    Requires(len(s) == 3)
    t = "abc"
    assert t[0] == "a"
    assert t[-1] == "c"
    assert len(s[1]) == 1
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert t[1] == "c"


def index_out_of_range(s: str) -> str:
    #:: ExpectedOutput(application.precondition:assertion.false)
    return s[0]


def slices(s: str) -> None:
    Requires(len(s) >= 2)
    t = "abcdef"
    assert t[1:3] == "bc"
    assert t[:2] == "ab"
    assert t[4:] == "ef"
    assert t[-2:] == "ef"
    assert t[3:1] == ""
    assert len(s[1:]) == len(s) - 1
    assert s[:1] + s[1:] == s
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert t[1:3] == "bd"


def slices_cut_to_fit(s: str) -> None:
    t = "abc"
    assert t[1:10] == "bc"
    assert t[5:] == ""
    assert t[-10:2] == "ab"
    assert ""[1:] == ""
    assert s[:len(s) + 5] == s
    assert len(s[:2]) <= 2
    if len(s) >= 2:
        assert len(s[:2]) == 2
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert len(s[:2]) == 2


def contains(s: str, t: str) -> None:
    assert "b" in "abc"
    assert "d" not in "abc"
    assert "" in s
    assert s in s
    if t in s:
        assert len(t) <= len(s)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert "a" in s


def contains_longer(s: str) -> None:
    Requires(len(s) >= 3)
    t = "abcd"
    # The slice is the witness.
    assert t[1:3] == "bc"
    assert "bc" in t
    assert s[1:3] in s
    assert "bd" not in "abc"
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert "bd" in t


def contains_longer_unaided() -> None:
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert "bc" in "abcd"


def affixes(s: str) -> None:
    t = "abcdef"
    assert t.startswith("abc")
    assert not t.startswith("abd")
    assert t.endswith("def")
    assert not t.endswith("abcdefg")
    assert s.startswith("")
    if s.startswith("ab"):
        assert len(s) >= 2
        assert s[0] == "a"
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert t.endswith("de")


def repeated(s: str, n: int) -> None:
    assert "ab" * 1 == "ab"
    assert "ab" * 2 == "abab"
    assert "ab" * 0 == ""
    assert s * -1 == ""
    assert len(s * 3) == 3 * len(s)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert "ab" * 2 == "aba"


def cased(s: str, t: str) -> None:
    Requires(s == t)
    assert s.lower() == t.lower()
    assert isinstance(s.upper(), str)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert s.lower() == s


def stripped(s: str) -> None:
    assert len(s.strip()) <= len(s)
    assert len(s.lstrip("x")) <= len(s)
    assert "".rstrip() == ""
    assert "ab".strip() == ("a" + "b").strip()
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert s.strip() == s


def replaced(s: str) -> None:
    assert "abc".replace("d", "x") == "abc"
    assert isinstance(s.replace("a", "b"), str)
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert s.replace("a", "b") == s


def classified(s: str) -> None:
    assert not "".isdigit()
    assert not "".isalpha()
    assert not "".isalnum()
    assert not "".isupper()
    assert not "".islower()
    assert not "".isspace()
    assert s.isupper() == (s + "").isupper()
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert s.isdigit()


def code_point(s: str) -> None:
    Requires(len(s) == 1)
    assert ord("a") == 97
    assert ord(s) == ord(s[0])
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert ord(s) == 97


def code_point_of_longer(s: str) -> int:
    #:: ExpectedOutput(application.precondition:assertion.false)
    return ord(s)
