# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Tuple


class A:

    def something(self, urgh: bool, i: int, a: 'A', b: bool) -> None:
        Requires(not urgh and b)
        Requires(i > -2)

    def something2(self, urgh: bool, *vars: object) -> None:
        Requires(len(vars) > 1)
        Requires(isinstance(vars[0], int))

    def something_call(self, args: Tuple[int, 'A']) -> None:
        Requires(args[0] > 0)
        self.something(False, *args, True)

    def something_call2(self, args: Tuple[int, 'A']) -> None:
        Requires(args[0] > -4)
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.something(False, *args, True)

    def something_call3(self, args: Tuple[int, 'A']) -> None:
        Requires(args[0] > 0)
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.something(False, *args, False)

    def something_call4(self) -> None:
        t1 = (False, 13)
        t2 = (A(), True)
        self.something(*t1, *t2)

    def something_call5(self) -> None:
        t1 = (True, 13)
        t2 = (A(), True)
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.something(*t1, *t2)

    def something2_call(self, tpl: Tuple[bool, int, 'A']) -> None:
        self.something2(*tpl)

    def something2_call2(self, tpl: Tuple[bool, int]) -> None:
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.something2(*tpl)

    def something2_call3(self, tpl: Tuple[bool, 'A', 'A']) -> None:
        #:: ExpectedOutput(call.precondition:assertion.false)
        self.something2(*tpl)

