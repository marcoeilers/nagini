# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from typing import Tuple

from nagini_contracts.contracts import Ensures, Requires, Result, Pure


def huh(t: Tuple[int, bool, int], i: int) -> int:
  Requires(0 <= i and i < 3)
  #:: ExpectedOutput(postcondition.violated:assertion.false)
  Ensures(int, lambda r: r >= 5)
  j: int = t[2]
  return j + 5


def huh2(t: Tuple[int, bool, int], i: int) -> int:
  Requires(0 <= i and i < 3)
  Requires(t[0] >= 0 and t[2] >= 0)
  Ensures(int, lambda r: r >= 5)
  j: int = t[1]
  k: bool = t[0] == 34
  return j + 5

@Pure
def huh3(t: Tuple[int, bool, int], i: int) -> int:
  Requires(0 <= i and i < 3)
  Requires(t[0] >= 0 and t[2] >= 0)
  Ensures(int, lambda r: r >= 5)
  j: int = t[2]
  return j + 5

@Pure
def huh4(t: Tuple[int, bool, int], i: int) -> int:
  Requires(0 <= i and i < 3)
  #:: ExpectedOutput(postcondition.violated:assertion.false)
  Ensures(int, lambda r: r >= 5)
  j: int = t[2]
  return j + 5