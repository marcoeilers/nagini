# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:

  def foo(self, secret: int) -> int:
    Ensures(Low(Result()))
    return 0


class B(A):

  def foo(self, secret: int) -> int:
    Ensures(Low(Result()))
    return 1


def main_incorrect(a: A, secret: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Low(Result()))
    return a.foo(secret)


def main_correct(a: A, secret: int) -> int:
    Requires(Low(type(a)))
    Ensures(Low(Result()))
    return a.foo(secret)
