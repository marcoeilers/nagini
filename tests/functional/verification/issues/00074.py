# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from typing import Tuple, Dict
from nagini_contracts.contracts import Requires, Ensures, Result

class Super:

    def foo(self, *args: Tuple[int]) -> int:
        Requires(len(args) > 3)
        #:: ExpectedOutput(postcondition.violated:assertion.false,L1)
        Ensures(Result() > 2)
        return 5

    def bar(self, **kwargs: Dict[str, int]) -> int:
        Requires(len(kwargs) > 3)
        #:: ExpectedOutput(postcondition.violated:assertion.false,L2)
        Ensures(Result() > 2)
        return 5


class Sub(Super):

    def foo(self, *args: Tuple[int]) -> int:
        Requires(len(args) > 2)
        Ensures(Result() > 4)
        return 5

    def bar(self, **kwargs: Dict[str, int]) -> int:
        Requires(len(kwargs) > 2)
        Ensures(Result() > 4)
        return 5


class Sub2(Super):

    #:: Label(L1)
    def foo(self, *args: Tuple[int]) -> int:
        Requires(len(args) > 2)
        Ensures(Result() > 0)
        return 5

    #:: Label(L2)
    def bar(self, **kwargs: Dict[str, int]) -> int:
        Requires(len(kwargs) > 2)
        Ensures(Result() > 0)
        return 5
