from py2viper_contracts.contracts import *
import resources.namespace_test_2
Import('namespace_test_2.py', 'resources.namespace_test_2')


class Sub(resources.namespace_test_2.Super):
    pass


GLOBAL = 42


def a_method() -> bool:
    Ensures(Result())
    return True


@Pure
def a_function() -> bool:
    return False


class SpecificException(Exception):
    pass
