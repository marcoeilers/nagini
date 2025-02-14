from abc import ABC
from typing import Generic, TypeVar, Tuple
from nagini_translation.native.vf.standard.value import ValueT


class Consumer(Generic[ValueT], ABC):
    def consume(self, * value: Tuple[ValueT, ...]) -> None:
        pass
