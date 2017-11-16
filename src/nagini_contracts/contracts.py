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
)


GHOST_PREFIX = "_gh_"

CONTRACT_WRAPPER_FUNCS = ['Requires', 'Ensures', 'Exsures', 'Invariant']

CONTRACT_FUNCS = ['Assume', 'Assert', 'Old', 'Result', 'Implies', 'Forall',
                  'Exists', 'Low', 'Acc', 'Rd', 'Fold', 'Unfold', 'Unfolding',
                  'Previous', 'RaisedException', 'Sequence', 'ToSeq', 'MaySet',
                  'MayCreate', 'CallSlot', 'CallSlotProof',
                  'UniversallyQuantified', 'ClosureCall', ]

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


def Previous(it: T) -> List[T]:
    """
    Within the body of a loop 'for x in xs', Previous(x) represents the list of
    the values of x in previous loop iterations.
    """
    pass


def Assume(expr: bool) -> None:
    pass


def Assert(expr: bool) -> bool:
    pass


def Old(expr: T) -> T:
    pass


def Result() -> Any:
    pass


def RaisedException() -> Exception:
    pass


def Implies(p: bool, q: bool) -> bool:
    """
    Logical implication p ==> q.
    """
    pass


def Forall(domain: Iterable[T],
           predicate: Callable[[T], Tuple[bool, List[List[Any]]]]) -> bool:
    """
    forall x in domain: predicate(x)
    """
    pass


def Exists(domain: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """
    exists x in domain: predicate(x)
    """
    pass


def Low(*args) -> bool:
    """
    Predicate to indicate that an expression has to be *low*.

    +    Calling with 0 args translates to ``!tl``.
    +    Calling with 1 arg translates to ``!tl &amp;&amp; expr == expr_p``.
    +    Ignored when not verifying information flow.
    """
    pass


class Sequence(Generic[T], Sized, Iterable[T]):
    """
    A Sequence[T] represents a pure sequence of instances of subtypes of T, and
    is translated to native Viper sequences.
    """

    def __init__(self, *args: T) -> None:
        """
        ``Sequence(a, b, c)`` creates a Sequence instance containing the objects
        a, b and c in that order.
        """

    def __contains__(self, item: object) -> bool:
        """
        True iff this Sequence contains the given object (not taking ``__eq__``
        into account).
        """

    def __getitem__(self, item: int) -> T:
        """
        Returns the item at the given position.
        """

    def __len__(self) -> int:
        """
        Returns the length of this Sequence.
        """

    def __add__(self, other: 'Sequence[T]') -> 'Sequence[T]':
        """
        Concatenates two Sequences of the same type to get a new Sequence.
        """

    def take(self, until: int) -> 'Sequence[T]':
        """
        Returns a new Sequence of the same type containing all elements starting
        from the beginning until the given index. ``Sequence(3,2,5,6).take(3)``
        is equal to ``Sequence(3,2,5)``.
        """

    def drop(self, until: int) -> 'Sequence[T]':
        """
        Returns a new Sequence of the same type containing all elements starting
        from the given index (i.e., drops all elements until that index).
        ``Sequence(2,3,5,6).drop(2)`` is equal to ``Sequence(5,6)``.
        """

    def update(self, index: int, new_val: T) -> 'Sequence[T]':
        """
        Returns a new sequence of the same type, containing the same elements
        except for the element at index ``index``, which is replaced by
        ``new_val``.
        """

    def __iter__(self) -> Iterator[T]:
        """
        Sequences can be quantified over; this is only here so that Sequences
        can be used as arguments for Forall.
        """


def ToSeq(l: Iterable[T]) -> Sequence[T]:
    """
    Converts the given iterable of a built-in type (list, set, dict, range) to
    a pure Sequence.
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


def NotPreservingTL(func: T) -> T:
    """
    Decorator indicating that this method/function does not (necessarily)
    preserve the timelevel.
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


def CallSlot(call_slot: Callable[..., None]) -> Callable[..., Any]:
    """
    Decorator to mark a method as a call slot declaration.
    """

    def call_slot_handler(*args, **kwargs) -> Any:

        def uq_handler(*args, **kwargs) -> None:
            pass

        return uq_handler

    return call_slot_handler


def UniversallyQuantified(uq: Callable[..., None]) -> None:
    """
    Decorator to mark a method as introducing universally quantified
    variables inside a call slot.
    """
    pass


def CallSlotProof(call_slot: Callable[..., Any]) -> Callable[[Callable[..., None]], None]:
    """
    Decorator to mark a method as a proof for a call slot.
    """
    pass


def ClosureCall(call: Any, justification: Any) -> Any:
    """
    Justifies a closure call through either
     * a CallSlot (justification == the callslot instance)
     * proofing static dispatch (justification == the static method)
    """
    pass


def list_pred(l: List[T]) -> bool:
    """
    Special, predefined predicate that represents the permissions belonging
    to a list. To be used like normal predicates, except it does not need to
    be folded or unfolded.
    """
    pass


def set_pred(s: Set[T]) -> bool:
    """
    Special, predefined predicate that represents the permissions belonging
    to a set. To be used like normal predicates, except it does not need to
    be folded or unfolded.
    """
    pass


def dict_pred(d: Dict[T, V]) -> bool:
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
        'Low',
        'Acc',
        'Rd',
        'Fold',
        'Unfold',
        'Unfolding',
        'Pure',
        'Predicate',
        'Ghost',
        'NotPreservingTL',
        'ContractOnly',
        'GhostReturns',
        'list_pred',
        'dict_pred',
        'set_pred',
        'Sequence',
        'ToSeq',
        'CallSlot',
        'UniversallyQuantified',
        'CallSlotProof',
        'ClosureCall',
        'MaySet',
        'MayCreate',
        ]
