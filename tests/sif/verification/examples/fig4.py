from nagini_contracts.contracts import *


class A:

  def foo(self, secret: int) -> int:
    Ensures(Low(Result()))
    return 0


class B(A):

  def foo(self, secret: int) -> int:
    Ensures(Low(Result()))
    return 1


class C(A):

  def foo(self, secret: int) -> int:
    return secret


def main_incorrect(a: A, secret: int) -> int:
    Ensures(Low(Result()))
    return a.foo(secret)


def main_correct(a: A, secret: int) -> int:
    Requires(Low(type(a)))
    Ensures(Low(Result()))
    return a.foo(secret)
