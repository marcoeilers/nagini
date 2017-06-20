from nagini_contracts.contracts import *
from nagini_contracts.io_builtins import *


class A:
    def __init__(self) -> None:
        self.v = 12
        self.v2 = self.vtt
        self.vtt = 77

    @property
    def vtt(self) -> int:
        Requires(Acc(self.v))
        return self.v * 2

    @vtt.setter
    def vtt(self, vhalvs: int) -> str:
        Requires(Acc(self.v))
        Ensures(Acc(self.v))
        Ensures(self.v == vhalvs // 2)
        self.v = vhalvs // 3
        #:: ExpectedOutput(invalid.program:invalid.return)
        return "asd"