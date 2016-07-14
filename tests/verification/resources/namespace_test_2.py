from py2viper_contracts.contracts import *
from resources.namespace_test_3 import a_function, P
# Import('namespace_test_3.py')


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
