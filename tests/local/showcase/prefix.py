from nagini_contracts.contracts import *

@Complex
class PrefixStuff:
    def __init__(self) -> None:
        Ensures(MayCreate(self, 'x'))
        Ensures(MayCreate(self, '__x'))

    def __getattr__(self, name: str) -> object:
        Requires(Implies(len(name) >= 2, name[:2] != "__"))
        return 10

def prefix_test() -> None:
    p = PrefixStuff()
    Assert(p.x == 10)
    # Assert(p.__x == 10)   # this will fail
