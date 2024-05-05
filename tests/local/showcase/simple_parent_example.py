from nagini_contracts.contracts import *

class SimpleParent:
    def __init__(self) -> None:
        self.x = "15"
        Ensures(Acc(self.x))
        Ensures(self.x == "15")

@Complex
class ComplexChild(SimpleParent):
    def __init__(self) -> None:
        super().__init__()
        Ensures(Acc(self.x))
        Ensures(self.x == "15")

def simple_parent_test() -> None:
    p = SimpleParent()
    c = ComplexChild()

    Assert(p.x == "15")
    Assert(c.x == "15")

    Assert(c.__dict__['x'] == "15")
    # Assert(p.__dict__['x'] == "15")   # will not work because SimpleParent is non-complex.
