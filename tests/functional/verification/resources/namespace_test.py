# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
import resources.namespace_test_2


class Sub(resources.namespace_test_2.Super):
    pass


@Predicate
def PP(i: int) -> bool:
    return resources.namespace_test_2.P(i)


GLOBAL = 42


def a_method() -> bool:
    Ensures(Result())
    return True


@Pure
def a_function() -> bool:
    return False


class SpecificException(Exception):
    pass
