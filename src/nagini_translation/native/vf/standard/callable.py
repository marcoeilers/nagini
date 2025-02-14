from abc import ABC
from collections import OrderedDict

class Callable(ABC):
    #TODO: what is type here exactly?
    def __init__(self, name: str, argtypes: OrderedDict[str, type]):
        self.name = name
        self.signature = argtypes

class Function(Callable):
    pass

