# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class SuperX:
    @Pure
    def foo(self, i: int) -> int:
        return i

class X(SuperX):
    @Pure
    def foo(self, i: int) -> int:
        return i + 1

class SubX(X):
    @Pure
    def foo(self, i: int) -> int:
        return i + 2

class Y:
    @Pure
    @Transparent
    def bar(self, i: int) -> int:
        return i + 3