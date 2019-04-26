# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def find_divisor(product: int) -> int:
    Requires(product >= 2)
    Ensures(Result() >= 2 and Result() <= product)
    Ensures(Forall(int, lambda x: (Implies(x >= 2 and x < Result(), product % x != 0), [[product % x]])))
    Ensures(Implies(Result() != product, product % Result() == 0))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    i = 2
    while i < product:
        Invariant(i >= 2 and i <= product)
        Invariant(Forall(int, lambda x: (Implies(x >= 2 and x < i, product % x != 0), [[product % x]])))
        if product % i == 0:
            break
        i += 1
    return i


def find_divisor_else(product: int) -> int:
    Requires(product >= 2)
    Ensures(Result() == -1 or (Result() >= 2 and Result() <= product))
    Ensures(Implies(Result() > 0, Forall(int, lambda x: (Implies(x >= 2 and x < Result(), product % x != 0), [[product % x]]))))
    Ensures(Implies(Result() == -1, Forall(int, lambda x: (Implies(x >= 2 and x < product, product % x != 0), [[product % x]]))))
    Ensures(Implies(Result() > 0, product % Result() == 0))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    i = 2
    while i < product:
        Invariant(i >= 2 and i <= product)
        Invariant(Forall(int, lambda x: (Implies(x >= 2 and x < i, product % x != 0), [[product % x]])))
        if product % i == 0:
            break
        i += 1
    else:
        return -1
    return i


def find_divisor_for(product: int) -> int:
    Requires(product > 2)
    Ensures(Result() >= 2 and Result() <= product)
    Ensures(Forall(int, lambda x: (Implies(x >= 2 and x < Result(), product % x != 0), [[product % x]])))
    Ensures(Implies(Result() != product, product % Result() == 0))
    for i in range(2, product):
        Invariant(i >= 2 and i <= product)
        Invariant(Forall(Previous(i), lambda x: (product % x != 0, [[product % x]])))
        if product % i == 0:
            Assert(Previous(i) == ToSeq(range(2, i)))
            break
    else:
        i = product
    return i


def find_divisor_for_2(product: int) -> int:
    Requires(product > 2)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(False)
    for i in range(2, product):
        Invariant(i >= 2 and i <= product)
        Invariant(Forall(Previous(i), lambda x: (product % x != 0, [[product % x]])))
        if product % i == 0:
            break
    else:
        i = product
    return i