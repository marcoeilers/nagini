"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Functions and classes needed for writing IO related contracts."""

# pragma pylint: disable=too-many-arguments,invalid-name,unused-argument,too-many-locals


from typing import Any, Callable, Generic, List, Tuple, Type, TypeVar, Union


BUILTIN_IO_OPERATIONS = (
    'no_op_io',
    'split_io',
    'join_io',
    'gap_io',
    'set_var_io',
)


IO_OPERATION_PROPERTY_FUNCS = [
    'Terminates',
    'TerminationMeasure',
]


IO_CONTRACT_FUNCS = [
    'ctoken',
    'token',
    'Open',
    'Eval',
    'eval_io',
]


T = TypeVar('T')
T1 = TypeVar('T1')
T2 = TypeVar('T2')
T3 = TypeVar('T3')
T4 = TypeVar('T4')
T5 = TypeVar('T5')
T6 = TypeVar('T6')
T7 = TypeVar('T7')
T8 = TypeVar('T8')
T9 = TypeVar('T9')
T10 = TypeVar('T10')
T11 = TypeVar('T11')
T12 = TypeVar('T12')
T13 = TypeVar('T13')
T14 = TypeVar('T14')
T15 = TypeVar('T15')


def IOForall(domain: Type[T],
             predicate: Callable[[T], Union[bool, Tuple[bool, List[List[Any]]]]]) -> bool:
    pass


def IOExists(domain: Type[T]) -> Callable[[Callable[[T], bool]], bool]:
    pass


class IOExists1(Generic[T1]):
    """``IOExists`` for defining 1 IO existential variable."""

    def __init__(
            self,
            t1: Type[T1]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1], Any]) -> bool:
        pass


class IOExists2(Generic[T1, T2]):
    """``IOExists`` for defining 2 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2], Any]) -> bool:
        pass


class IOExists3(Generic[T1, T2, T3]):
    """``IOExists`` for defining 3 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2, T3], Any]) -> bool:
        pass


class IOExists4(Generic[T1, T2, T3, T4]):
    """``IOExists`` for defining 4 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2, T3, T4], Any]) -> bool:
        pass


class IOExists5(Generic[T1, T2, T3, T4, T5]):
    """``IOExists`` for defining 5 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2, T3, T4, T5], Any]) -> bool:
        pass


class IOExists6(Generic[T1, T2, T3, T4, T5, T6]):
    """``IOExists`` for defining 6 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2, T3, T4, T5, T6], Any]) -> bool:
        pass


class IOExists7(Generic[T1, T2, T3, T4, T5, T6, T7]):
    """``IOExists`` for defining 7 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2, T3, T4, T5, T6, T7], Any]) -> bool:
        pass


class IOExists8(Generic[T1, T2, T3, T4, T5, T6, T7, T8]):
    """``IOExists`` for defining 8 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2, T3, T4, T5, T6, T7, T8], Any]) -> bool:
        pass


class IOExists9(Generic[T1, T2, T3, T4, T5, T6, T7, T8, T9]):
    """``IOExists`` for defining 9 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8],
            t9: Type[T9]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[[T1, T2, T3, T4, T5, T6, T7, T8, T9], Any]) -> bool:
        pass


class IOExists10(Generic[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10]):
    """``IOExists`` for defining 10 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8],
            t9: Type[T9],
            t10: Type[T10]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[
                [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10],
                Any]) -> bool:
        pass


class IOExists11(Generic[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11]):
    """``IOExists`` for defining 11 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8],
            t9: Type[T9],
            t10: Type[T10],
            t11: Type[T11]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[
                [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11],
                Any]) -> bool:
        pass


class IOExists12(Generic[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12]):
    """``IOExists`` for defining 12 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8],
            t9: Type[T9],
            t10: Type[T10],
            t11: Type[T11],
            t12: Type[T12]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[
                [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12],
                Any]) -> bool:
        pass


class IOExists13(Generic[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12,
                         T13]):
    """``IOExists`` for defining 13 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8],
            t9: Type[T9],
            t10: Type[T10],
            t11: Type[T11],
            t12: Type[T12],
            t13: Type[T13]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[
                [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13],
                Any]) -> bool:
        pass


class IOExists14(Generic[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12,
                         T13, T14]):
    """``IOExists`` for defining 14 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8],
            t9: Type[T9],
            t10: Type[T10],
            t11: Type[T11],
            t12: Type[T12],
            t13: Type[T13],
            t14: Type[T14]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[
                [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13,
                 T14],
                Any]) -> bool:
        pass


class IOExists15(Generic[T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12,
                         T13, T14, T15]):
    """``IOExists`` for defining 15 IO existential variables."""

    def __init__(
            self,
            t1: Type[T1],
            t2: Type[T2],
            t3: Type[T3],
            t4: Type[T4],
            t5: Type[T5],
            t6: Type[T6],
            t7: Type[T7],
            t8: Type[T8],
            t9: Type[T9],
            t10: Type[T10],
            t11: Type[T11],
            t12: Type[T12],
            t13: Type[T13],
            t14: Type[T14],
            t15: Type[T15]) -> None:
        pass

    def __call__(
            self,
            expr: Callable[
                [T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13,
                 T14, T15],
                Any]) -> bool:
        pass


def Open(operation: bool) -> None:
    """Replace non basic IO operation with its contents."""


def GetGhostOutput(operation: bool, output_name: str) -> Any:
    """Bind an expected IO operation output to a variable.

    Example usage::

        t2 = GetGhostOutput(read_int_io(t1), 't_post')
    """


def IOOperation(func: T) -> T:
    """Decorator to mark IO operations. It's a no-op."""
    return func


def Terminates(value: bool) -> None:
    """Provide IO operation termination condition."""


def TerminationMeasure(value: int) -> None:
    """Provide IO operation termination measure."""


class Place:
    """Denotes a place in a Petri Net."""


TOP_MEASURE = -1


def token(t: Place, measure: int = TOP_MEASURE) -> bool:
    """Indicate that there is a token at place ``t``."""


def ctoken(t: Place) -> bool:
    """Indicate that there is a credit token at place ``t``."""


__all__ = (
    'IOForall',
    'IOExists',
    'IOExists1',
    'IOExists2',
    'IOExists3',
    'IOExists4',
    'IOExists5',
    'IOExists6',
    'IOExists7',
    'IOExists8',
    'IOExists9',
    'IOExists10',
    'IOExists11',
    'IOExists12',
    'IOExists13',
    'IOExists14',
    'IOExists15',
    'Open',
    'GetGhostOutput',
    'IOOperation',
    'Terminates',
    'TerminationMeasure',
    'Place',
    'token',
    'ctoken',
)
