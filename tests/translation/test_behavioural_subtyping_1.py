

class SuperA:
    def __init__(self) -> None:
        self.intfield = 14
        self.boolfield = True

    def someMethod(self, a: int) -> int:
        return a


class SubA(SuperA):
    def someMethod(self, b: int) -> int:
        return b + 5

class SubSubA(SubA):
    def someMethod(self, b: int) -> int:
        return b + 9

class SuperF:
    def someMethod(self, b: SubA, a: SubSubA) -> SubA:
        return a

class SubF1(SuperF):
    #:: ExpectedOutput(type.error:Return type of "someMethod" incompatible with supertype "SuperF")
    def someMethod(self, a : SubA, b : SubSubA) -> SuperA:
        return b