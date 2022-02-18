from nagini_contracts.contracts import *

class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val is 0)

def mytest(x: bool, y: bool, c: Cell) -> None:
    Requires(SplitOn(x, SplitOn(True), falseSplit=SplitOn(y)))
    Requires(Acc(c.val))
    Assume(SplitOn(c.val > 6))
    if x:
        #:: ExpectedOutput(assert.failed:assertion.false)|ExpectedOutput(assert.failed:assertion.false)
        Assert(c.val == 8)
    else:
        if y:
            #:: ExpectedOutput(assert.failed:assertion.false)|ExpectedOutput(assert.failed:assertion.false)
            Assert(c.val == 9)
        else:
            #:: ExpectedOutput(assert.failed:assertion.false)|ExpectedOutput(assert.failed:assertion.false)
            Assert(c.val == 10)


def mytestcaller() -> None:
    c = Cell()
    mytest(True, False, c)