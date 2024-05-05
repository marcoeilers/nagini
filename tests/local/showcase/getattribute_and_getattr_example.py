from nagini_contracts.contracts import *

@Complex
class GetattributeStuff:
    def __init__(self) -> None:
        self.x = 1
        Ensures(Acc(self.x))
        Ensures(self.x == 1)
        Ensures(MayCreate(self, 'y'))
        Ensures(MayCreate(self, 'z'))

    def foo(self) -> object:
        Ensures(Result() == 50)
        return 50

    def __getattr__(self, name: str) -> object:
        return 10

    def __getattribute__(self, name: str) -> object:
        Requires(MaySet(self, name))

        # Auto generated:
        # Ensures(
        #     Implies(
        #         name in PSet("foo", "__dict__", ...),
        #         Result() == object.__getattribute__(self, name))
        # )

        if name == "z":
            return 1_000
        else:
            return object.__getattribute__(self, name)


def getattribute_example() -> None:
    g = GetattributeStuff()

    Assert(g.x == 1)       # g.__getattribute__('x') == 10     WITH __getattr__
    Assert(g.y == 10)      # g.__getattribute__('y') == 1_000  WITH __getattr__
    Assert(g.z == 1_000)   # g.__getattribute__('z') == 1_000  WITH __getattr__

    Assert(g.foo() == 50)         # does not call __getattribute__
    Assert(g.__dict__['x'] == 1)  # does not call __getattribute__

    Assert(object.__getattribute__(g, "x") == 1)     # same as g.__dict__['x']
    # Assert(object.__getattribute__(g, "y") == 1_000)      # will not work
    # Assert(object.__getattribute__(g, "z") == 1_000_000)  # will not work
