# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "A Theorem Proving Approach to Analysis of Secure Information Flow"
Darvas, Adam and Haehnle, Reiner and Sands, David
Security in Pervasive Computing, 2005
"""

from nagini_contracts.contracts import *

class Account():
    def __init__(self) -> None:
        self.balance = 0
        self.extraService = False

    def writeBalance(self, amount: int) -> None:
        # balance and amount are high -> low extraService reveals information about high variable
        Requires(Acc(self.balance))
        Requires(Acc(self.extraService))
        Requires(Low(self.extraService))
        Ensures(Acc(self.balance))
        Ensures(Acc(self.extraService))
        #:: ExpectedOutput(postcondition.violated:assertion.false)
        Ensures(Low(self.extraService))
        if amount >= 10000:
            self.extraService = True
        else:
            self.extraService = False
        self.balance = amount

    def writeBalance_fixed(self, amount: int) -> None:
        # balance and amount are high -> low extraService reveals information about high variable
        Requires(Acc(self.balance))
        Requires(Acc(self.extraService))
        Requires(Low(self.extraService))
        Ensures(Acc(self.balance))
        Ensures(Acc(self.extraService))
        Ensures(Low(self.extraService))
        Declassify(amount >= 10000)
        if amount >= 10000:
            self.extraService = True
        else:
            self.extraService = False
        self.balance = amount

    def readBalance(self) -> int:
        Requires(Acc(self.balance))
        Ensures(Acc(self.balance))
        return self.balance

    def readExtra(self) -> bool:
        Requires(Acc(self.extraService))
        Ensures(Acc(self.extraService))
        return self.extraService
