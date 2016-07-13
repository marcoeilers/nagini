from py2viper_contracts.contracts import *
from resources.namespace_test_3 import a_function
Import('namespace_test_3.py')


class Super:
    def get(self) -> int:
        Ensures(Implies(a_function(), Result() == 56))
        return 56