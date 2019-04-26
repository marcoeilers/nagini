# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

a = 12

def main() -> None:
    #:: ExpectedOutput(invalid.program:permission.to.final.var)
    Requires(Acc(a))