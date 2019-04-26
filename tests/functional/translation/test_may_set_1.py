# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

class B:
    def __init__(self) -> None:
        #:: ExpectedOutput(invalid.program:invalid.may.set)
        Ensures(MaySet(self, 'a' + 'b'))
        pass

    def set(self) -> None:
        self.ab = 12