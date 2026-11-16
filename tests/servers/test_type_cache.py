"""TypeInfo's mypy cache eviction (no JVM needed)."""

from nagini_translation.lib.typeinfo import TypeInfo


HELPER = """from nagini_contracts.contracts import *


@Pure
def f(x: int) -> int:
    return x
"""
MIDDLE = "from helper import f\n"
MAIN = "import middle\n"


def test_identical_module_cached_from_another_project(tmp_path, monkeypatch):
    """A module cached from an identical file elsewhere is re-checked, also
    when the walk from the main file cannot reach it."""
    monkeypatch.chdir(tmp_path)
    for d in ("a", "b"):
        (tmp_path / d).mkdir()
        (tmp_path / d / "helper.py").write_text(HELPER)
        (tmp_path / d / "middle.py").write_text(MIDDLE)
        (tmp_path / d / "main.py").write_text(MAIN)
    assert TypeInfo().check(str(tmp_path / "a" / "helper.py"), str(tmp_path / "a"))
    types = TypeInfo()
    assert types.check(str(tmp_path / "b" / "main.py"), str(tmp_path / "b"))
    assert types.get_func_type(["helper", "f"]) is not None
