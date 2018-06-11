from nagini_contracts.contracts import *

class A:
    def dynamic_foo(self) -> int:
        Requires(LowEvent())
        Ensures(Low(Result()))
        return 0

def static_foo() -> int:
    Requires(LowEvent())
    Ensures(Low(Result()))
    return 0
