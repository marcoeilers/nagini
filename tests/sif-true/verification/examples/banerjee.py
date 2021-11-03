# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example from "Secure Information Flow and Pointer Confinement in a Java-like Language"
A. Banerjee and D. A. Naumann
CSFW 2002
"""
from nagini_contracts.contracts import *

from typing import Optional

class Patient:
    def __init__(self, name: str) -> None:
        self.name = name
        Ensures(Acc(self.name))
        Ensures(self.name == name)

    def getName(self) -> str:
        Requires(Acc(self.name, 1/4))
        Ensures(Acc(self.name, 1/4))
        Ensures(Result() == self.name)
        return self.name

    def setName(self, n: str) -> None:
        Requires(Acc(self.name))
        Requires(LowVal(n))
        Ensures(Acc(self.name))
        Ensures(self.name is n)
        self.name = n

class XPatient(Patient):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.hiv = ""
        Ensures(Acc(self.name))
        Ensures(Acc(self.hiv))

    def setHIV(self, s: str) -> None:
        Requires(Acc(self.hiv))
        Ensures(Acc(self.hiv))
        self.hiv = s

    def getHIV(self) -> str:
        Requires(Acc(self.hiv, 1/4))
        Ensures(Acc(self.hiv, 1/4))
        Ensures(Result() == self.hiv)
        return self.hiv

def readFile() -> Patient:
    Ensures(Low(Result()))
    Ensures(Acc(Result().name))
    Ensures(LowVal(Result().name))
    return Patient("Steve")

def readFromTrustedChan() -> str:
    # result is high
    return "high"

class Main:
    def main(self) -> None:
        lbuf = None # type: Optional[str]
        hbuf = None # type: Optional[str]
        # result of readFile is low
        lp = readFile()
        xp = XPatient("Dave")
        lbuf = lp.getName()
        hbuf = xp.getName()
        xp.setName(lbuf)
        # result of readFromTrustedChan is high
        hbuf = readFromTrustedChan()
        # HIV info of xp is set to high value
        xp.setHIV(hbuf)
        lbuf = hbuf
        #:: ExpectedOutput(call.precondition:assertion.false)
        lp.setName(xp.getHIV()) # argument of setName needs to be low -> fails

    def main_fixed(self) -> None:
        lbuf = None # type: Optional[str]
        hbuf = None # type: Optional[str]
        # result of readFile is low
        lp = readFile()
        xp = XPatient("Dave")
        lbuf = lp.getName()
        hbuf = xp.getName()
        xp.setName(lbuf)
        # result of readFromTrustedChan is high
        hbuf = readFromTrustedChan()
        # HIV info of xp is set to high value
        xp.setHIV(hbuf)
        lbuf = hbuf
        tmp_hiv = xp.getHIV()
        Declassify(tmp_hiv)
        lp.setName(tmp_hiv)
