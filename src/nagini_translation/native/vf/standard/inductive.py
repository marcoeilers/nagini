from abc import ABC
from typing import Generic, TypeVar
from nagini_translation.native.vf.standard.value import Value


class Inductive(Value, ABC):
    pass


