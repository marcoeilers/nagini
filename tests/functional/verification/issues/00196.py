# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import *

class T():
  def foo(self, idx: Tuple[Union[int, slice], ...]) -> Tuple[int, ...]:
    Requires(False)
    ...

t = T()
#:: ExpectedOutput(call.precondition:assertion.false)
r = t.foo((1, 2))
