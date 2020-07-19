# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    @staticmethod
    def static_method(a: A) -> int:
        return 17


class B(A):
    #:: ExpectedOutput(type.error:Signature of "static_method" incompatible with supertype "A")
    @staticmethod
    def static_method() -> int:
        return 17
