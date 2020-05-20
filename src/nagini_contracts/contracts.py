"""
Copyright (c) 2019 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List, Set,
    Sized,
    Tuple,
    Type,
    TypeVar,
    Union,
)


GHOST_PREFIX = "_gh_"

CONTRACT_WRAPPER_FUNCS = ['Requires', 'Ensures', 'Exsures', 'Invariant']

CONTRACT_FUNCS = ['Assume', 'Assert', 'Old', 'Result', 'Implies', 'Forall', 'IOForall',
                  'Exists', 'Low', 'LowVal', 'LowEvent', 'Declassify', 'TerminatesSif',
                  'Acc', 'Rd', 'Wildcard', 'Fold', 'Unfold', 'Unfolding', 'Previous',
                  'RaisedException', 'PSeq', 'PSet', 'ToSeq', 'MaySet', 'MayCreate',
                  'getMethod', 'getArg', 'getOld', 'arg', 'Joinable', 'MayStart', 'Let',
                  'PMultiset', 'LowExit',]

T = TypeVar('T')
V = TypeVar('V')


def Requires(expr: bool) -> bool:
    pass


def Ensures(expr: bool) -> bool:
    pass


def Exsures(exception: type, expr: bool) -> bool:
    pass


def Invariant(expr: bool) -> bool:
    pass


def Assume(expr: bool) -> None:
    pass


def Assert(expr: bool) -> bool:
    pass


def Old(expr: T) -> T:
    pass


def Result() -> Any:
    pass


def RaisedException() -> Any:
    pass


def Implies(p: bool, q: bool) -> bool:
    """
    Logical implication p ==> q.
    """
    pass


def Let(e1: T, t: Type[V], e2: Callable[[T], V]) -> V:
    """
    Allows defining an alias for a (pure) expression e1 to use in
    another expression or assertion e2.
    Let(5, int, lambda x : x + 34) means let x = 5 in x + 34
    """
    pass

def Forall(domain: 'Union[Iterable[T], Type[T]]',
           predicate: Callable[[T], Union[bool, Tuple[bool, List[List[Any]]]]]) -> bool:
    """
    forall x in domain: predicate(x)
    """
    pass


def Exists(domain: 'Union[Iterable[T], Type[T]]', predicate: Callable[[T], bool]) -> bool:
    """
    exists x in domain: predicate(x)
    """
    pass


def Low(expr: T) -> bool:
    """
    Predicate to indicate that an expression has to be *low*.
    Ignored when not verifying information flow.
    """
    pass

def LowVal(expr: T) -> bool:
    """
    Predicate to indicate that an expression has to be low, using value equality if the
    expression is a primitive. Ignored when not verifying information flow.
    """
    pass

def LowEvent() -> bool:
    """
    Predicate that states that either both executions reach this point or none of them.
    """
    pass

def LowExit() -> bool:
    """
    Predicate that states that whether the current loop has been left via a break or
    return statement does not depend on high data.
    """
    pass

def Declassify(expr: T) -> bool:
    """
    Declassify an expression. Assumes expression to be low.
    """
    pass

def TerminatesSif(cond: bool, rank: int) -> bool:
    """
    Verify absence of termination channels. Gives surrounding loop/call a
    termination condition and a ranking function.
    """
    pass

class PSeq(Generic[T], Sized, Iterable[T]):
    """
    A PSeq[T] represents a pure sequence of instances of subtypes of T, and
    is translated to native Viper sequences.
    """

    def __init__(self, *args: T) -> None:
        """
        ``PSeq(a, b, c)`` creates a PSeq instance containing the objects
        a, b and c in that order.
        """

    def __contains__(self, item: object) -> bool:
        """
        True iff this PSeq contains the given object (not taking ``__eq__``
        into account).
        """

    def __getitem__(self, item: int) -> T:
        """
        Returns the item at the given position.
        """

    def __len__(self) -> int:
        """
        Returns the length of this PSeq.
        """

    def __add__(self, other: 'PSeq[T]') -> 'PSeq[T]':
        """
        Concatenates two PSeqs of the same type to get a new PSeq.
        """

    def take(self, until: int) -> 'PSeq[T]':
        """
        Returns a new PSeq of the same type containing all elements starting
        from the beginning until the given index. ``PSeq(3,2,5,6).take(3)``
        is equal to ``PSeq(3,2,5)``.
        """

    def drop(self, until: int) -> 'PSeq[T]':
        """
        Returns a new PSeq of the same type containing all elements starting
        from the given index (i.e., drops all elements until that index).
        ``PSeq(2,3,5,6).drop(2)`` is equal to ``PSeq(5,6)``.
        """

    def update(self, index: int, new_val: T) -> 'PSeq[T]':
        """
        Returns a new sequence of the same type, containing the same elements
        except for the element at index ``index``, which is replaced by
        ``new_val``.
        """

    def __iter__(self) -> Iterator[T]:
        """
        PSeqs can be quantified over; this is only here so that PSeqs
        can be used as arguments for Forall.
        """

def Previous(it: T) -> PSeq[T]:
    """
    Within the body of a loop 'for x in xs', Previous(x) represents the list of
    the values of x in previous loop iterations.
    """
    pass


class PSet(Generic[T], Sized, Iterable[T]):
    """
    A PSet[T] represents a pure set of instances of subtypes of T, and is translated to
    native Viper sets.
    """

    def __init__(self, *args: T) -> None:
        """
        ``PSet(a, b, c)`` creates a set instance containing the objects
        a, b and c.
        """

    def __contains__(self, item: object) -> bool:
        """
        True iff this set contains the given object (not taking ``__eq__``
        into account).
        """

    def __len__(self) -> int:
        """
        Returns the cardinality of this set.
        """

    def __add__(self, other: 'PSet[T]') -> 'PSet[T]':
        """
        Returns the union of this set and the other.
        """

    def __sub__(self, other: 'PSet[T]') -> 'PSet[T]':
        """
        Returns the difference between this set and the other,
        """

    def __iter__(self) -> Iterator[T]:
        """
        Sets can be quantified over; this is only here so that sets
        can be used as arguments for Forall.
        """

class PMultiset(Generic[T], Sized, Iterable[T]):
    """
    An PMultiset[T] represents a pure multiset of instances of subtypes of T, and is translated to
    native Viper multisets.
    """

    def __init__(self, *args: T) -> None:
        """
        ``PMultiset(a, b, c)`` creates a multiset instance containing the objects
        a, b and c.
        """

    def num(self, item: object) -> int:
        """
        Returns the number of occurrences of ``item`` in this multiset.
        """

    def __len__(self) -> int:
        """
        Returns the cardinality of this set.
        """

    def __add__(self, other: 'PMultiset[T]') -> 'PMultiset[T]':
        """
        Returns the union of this multiset and the other.
        """

    def __sub__(self, other: 'PMultiset[T]') -> 'PMultiset[T]':
        """
        Returns the difference between this multiset and the other,
        """

    def __iter__(self) -> Iterator[T]:
        """
        Multisets can be quantified over; this is only here so that multisets
        can be used as arguments for Forall.
        """


def ToSeq(l: Iterable[T]) -> PSeq[T]:
    """
    Converts the given iterable of a built-in type (list, set, dict, range) to
    a pure PSeq.
    """


# The following annotations have no runtime semantics. They are only used for
# the Python to Viper translation.

def Acc(field, ratio=1) -> bool:
    """
    Access permission to field.
    0 < ratio < 1 means read-only access.
    ratio == 1 mean read-write access.
    """
    pass


def MayCreate(o: object, field_name: str) -> bool:
    """
    Permission to create a field called field_name on object o.
    """
    pass

def MaySet(o: object, field_name: str) -> bool:
    """
    Permission to either create a field called field_name on object o or access the
    existing field with that name.
    """
    pass


def Rd(field) -> bool:
    """
    Read permission to a predicate or field, only to be used in pure contexts.
    """
    pass


def ARP(counting: int = None) -> float:
    """
    Abstract read permission, only to be used in Acc(f, ...).
    """
    pass


"""
Permission used in predicates
"""
RD_PRED = 1  # type: float


def Wildcard(field) -> bool:
    """
    Wildcard permission to a predicate or field, only to be used in pure contexts.
    """
    pass


def Fold(predicate: bool) -> None:
    pass


def Unfold(predicate: bool) -> None:
    pass


def Unfolding(predicate: bool, expr: T) -> T:
    """
    Evaluates expr in a state where predicate has been unfolded.
    """
    return expr


def Pure(func: T) -> T:
    """
    Decorator to mark pure functions. It's a no-op.
    """
    return func


def Predicate(func: T) -> T:
    """
    Decorator to mark predicate functions. It's a no-op.
    """
    return func


def Ghost(func: T) -> T:
    """
    Decorator for ghost functions. It's a no-op.
    """
    return func

def AllLow(func: T) -> T:
    """
    Decorator indicating that everything this method does is low.
    Requires all inputs to be low, ensures all state it has access to and
    all return values are low.
    """
    return func

def PreservesLow(func: T) -> T:
    """
    Decorator indicating that everything this method does preserves lowness.
    Given that all the state it gets to work on is low to begin with, all state and
    return values will remain low.
    """
    return func

def ContractOnly(func: T) -> T:
    """
    Decorator to mark contract only methods. It's a no-op.
    """
    return func


def GhostReturns(start_index: int) -> Callable[[T], T]:
    """
    Decorator for functions which specifies which return values are ghost
    returns, starting at index 0. It's a no-op.
    If a function returns an n-tuple, @GhostReturns(k) means that
    elements 0 to k-1 are normal return values, elements k to n-1 are ghost
    return values. k must be less than n. If the function returns a value
    that is not a tuple, start_index can only be 0 (meaning that the only value
    that is returned is a ghost value). Using this decorator on functions which
    do not return anything is not allowed.
    """
    def wrap(func: T) -> T:
        return func
    return wrap


def list_pred(l: object) -> bool:
    """
    Special, predefined predicate that represents the permissions belonging
    to a list. To be used like normal predicates, except it does not need to
    be folded or unfolded.
    """
    pass


def set_pred(s: object) -> bool:
    """
    Special, predefined predicate that represents the permissions belonging
    to a set. To be used like normal predicates, except it does not need to
    be folded or unfolded.
    """
    pass


def dict_pred(d: object) -> bool:
    """
    Special, predefined predicate that represents the permissions belonging
    to a dict. To be used like normal predicates, except it does not need to
    be folded or unfolded.
    """


__all__ = [
        'Requires',
        'Ensures',
        'Exsures',
        'Invariant',
        'Previous',
        'Assume',
        'Assert',
        'Old',
        'Result',
        'RaisedException',
        'Implies',
        'Forall',
        'Exists',
        'Let',
        'Low',
        'LowVal',
        'LowEvent',
        'LowExit',
        'Declassify',
        'TerminatesSif',
        'AllLow',
        'PreservesLow',
        'Acc',
        'Rd',
        'ARP',
        'RD_PRED',
        'Wildcard',
        'Fold',
        'Unfold',
        'Unfolding',
        'Pure',
        'Predicate',
        'Ghost',
        'ContractOnly',
        'GhostReturns',
        'list_pred',
        'dict_pred',
        'set_pred',
        'PSeq',
        'PSet',
        'PMultiset',
        'ToSeq',
        'MaySet',
        'MayCreate',
        ]
