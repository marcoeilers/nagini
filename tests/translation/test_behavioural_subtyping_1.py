class SuperA:
    def __init__(self) -> None:
        self.intfield = 14
        self.boolfield = True

    def somemethod(self, a: int) -> int:
        return a


class SubA(SuperA):
    def somemethod(self, b: int) -> int:
        return b + 5


class SubSubA(SubA):
    def somemethod(self, b: int) -> int:
        return b + 9


class SuperF:
    def somemethod(self, b: SubA, a: SubSubA) -> SubA:
        return a


class SubF1(SuperF):
    #:: ExpectedOutput(type.error:Return type of "somemethod" incompatible with supertype "SuperF")
    def somemethod(self, a: SubA, b: SubSubA) -> SuperA:
        return b
