from nagini_contracts.contracts import *

@Complex
class MyClass:
    def __init__(self) -> None:
        self.x = 10
        Ensures(Acc(self.x))
        Ensures(self.x == 10)

@Complex
class WrapperMyClass:
    def __init__(self, wraps: MyClass) -> None:
        self.c = wraps
        Ensures(Acc(self.c))
        Ensures(self.c is wraps)
        Ensures(MayCreate(self, 'x'))

    def __getattr__(self, name: str) -> object:
        Requires(Acc(self.__dict__['c']))
        Requires(Acc(self.__dict__['c'].__dict__[name]))
        return self.c.__dict__[name]

def wrapper_test() -> None:
    c = MyClass()
    wc = WrapperMyClass(c)
    Assert(wc.x == 10)
