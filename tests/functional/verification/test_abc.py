# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

from abc import ABC, ABCMeta, abstractmethod


class C1(ABC):
    @abstractmethod
    def foo(self) -> int:
        #:: ExpectedOutput(postcondition.violated:assertion.false,L1)
        Ensures(Result() > 7)
        pass

    def baz(self) -> int:
        Ensures(Result() > 7)
        return 8

class C2(C1):
    def foo(self) -> int:
        Ensures(Result() > 8)
        return 9

class C3(C1):
    #:: Label(L1)
    def foo(self) -> int:
        Ensures(Result() > 5)
        return 6


class D1(metaclass=ABCMeta):
    @abstractmethod
    def bar(self) -> int:
        Ensures(Result() > 7)
        pass

    @abstractmethod
    def bark(self) -> int:
        Ensures(Result() > 7)
        pass

    def bam(self) -> int:
        Ensures(Result() > 7)
        return 9

class D2(D1):
    def bar(self) -> int:
        Ensures(Result() > 10)
        return 11

class D3(D2):
    def bark(self) -> int:
        Ensures(Result() > 33)
        return 99
