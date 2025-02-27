from abc import ABC
from nagini_translation.native.vf.standard.value import Value


class Literal(Value, ABC):
    def __init__(self, value):
        self.value = value
    def __eq__(self, other):
        return other.value == self.value
    def __str__(self):
        return str(self.value)

class Int(Literal):
    pass

class Bool(Literal):
    def __str__(self):
        return "true" if self.value else "false"
class Float(Literal):
    pass
class Char(Literal):
    pass
