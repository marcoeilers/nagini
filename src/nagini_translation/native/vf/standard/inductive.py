from abc import ABC
from typing import Generic, TypeVar
from nagini_translation.native.vf.standard.value import Value
from nagini_translation.native.vf.standard.valueloc import ValueLocation
ValueT = TypeVar("ValueT", bound="Value")
ValueT2 = TypeVar("ValueT2", bound="Value")


class Inductive(Value, ABC):
    pass


