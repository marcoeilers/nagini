# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from resources.namespace_test_3 import a_function, P


@Predicate
def B(i: int) -> bool:
    return i == 2


class Super:
    def get(self) -> int:
        Ensures(Implies(a_function(), Result() == 56))
        return 56

    @Predicate
    def some_pred(self, i: int) -> bool:
        return i > OTHER_GLOBAL


OTHER_GLOBAL = 34
