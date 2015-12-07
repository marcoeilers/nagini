from contracts import *

@Pure
def test_func(a : int, b : int, c: int) -> int:
    return a + b * 3 - c
