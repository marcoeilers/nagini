from nagini_contracts.contracts import *


class B:
    def __init__(self) -> None:
        #:: ExpectedOutput(invalid.program:invalid.may.create)
        Ensures(MayCreate(self, 'ab'))
        pass

    def set(self) -> None:
        self.ac = 12