from nagini_contracts.contracts import *

@Complex
class LockClass:
    def __init__(self) -> None:
        self.__dict__['lock'] = False
        self.foo = 10
        self.__dict__['lock'] = True
        Ensures(Acc(self.foo))
        Ensures(self.foo == 10)
        Ensures(Acc(self.__dict__['lock']))
        Ensures(self.__dict__['lock'] == True)

    # def __getattr__(self, item: str) -> object:
    #     return None

    def __setattr__(self, name: str, value: int) -> None:
        Requires(MaySet(self, name))
        Requires(Acc(self.lock))
        Requires(self.lock == False)

        self.__dict__[name] = value

        Ensures(Acc(self.lock))
        Ensures(Acc(self.__dict__[name]))
        Ensures(self.__dict__[name] is value)

def lock_test() -> None:
    l = LockClass()
    Assert(l.foo == 10)

    l.__dict__['lock'] = False  # without this, lines below will fail
    l.foo = 31
    Assert(l.foo == 31)
