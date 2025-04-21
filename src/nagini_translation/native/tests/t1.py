from nagini_contracts.contracts import *


class mytupledclass:
        def __init__(self, arg: int) -> None:
                self.arg = arg

        #@ContractOnly
        #@Native
        #def somefun(self, arg: int) -> int:
        #        Requires(Acc(self.arg))
        #        Ensures(Acc(self.arg) and self.arg == arg)
