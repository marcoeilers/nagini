# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "A Hybrid Approach for Proving Noninterference of Java Programs"
R. Kuesters, T. Truderung, B. Beckert, D. Bruns, M. Kirsten, and M. Mohr
2015 IEEE 28th Computer Security Foundations Symposium
"""

from nagini_contracts.contracts import *

class Example():
    def __init__(self) -> None:
        self.result = 0
        self.a = 0
        Ensures(Acc(self.result))
        Ensures(Acc(self.a))

    def main(self, secret: int) -> None:
        Requires(Acc(self.a))
        Requires(Acc(self.result))
        Requires(Low(self.result))
        Ensures(Acc(self.a))
        Ensures(Acc(self.result))
        Ensures(LowVal(self.result))
        self.a = 42
        self.bar(secret)
        b = self.foo(secret)
        self.result = b

    def foo(self, secret: int) -> int:
        Requires(Acc(self.a, 1/4))
        Ensures(Acc(self.a, 1/4))
        Ensures(Implies(Low(Old(self.a)), LowVal(Result())))
        b = self.a
        if secret == 0:
            b += secret
        return b

    def bar(self, secret: int) -> None:
        pass
