# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    @staticmethod
    def static_method() -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false, L1)
        Ensures(Result() > 1)
        return 17


class B(A):
    @staticmethod
    def static_method() -> int:
        Ensures(Result() > 6)
        return 66


class C(A):
    #:: Label(L1)
    @staticmethod
    def static_method() -> int:
        Ensures(Result() > 0)
        return 666
