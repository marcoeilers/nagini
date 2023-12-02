# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Dict


class CustomException:
    pass


CustomExceptionInstance = CustomException()


class Dynamic:
    def __init__(self, some_integer: int) -> None:
        # noinspection PyDictCreation
        self.custom__dict__ = {}                                # type: Dict[int, object]
        self.custom__dict__[76] = some_integer
        Ensures(Acc(self.custom__dict__))
        Ensures(Acc(dict_pred(self.custom__dict__)))
        Ensures(76 in self.custom__dict__)
        Ensures(isinstance(self.custom__dict__[76], int))
        Ensures(self.custom__dict__[76] == some_integer)
        Ensures(ToMap(self.custom__dict__).keys() == PSet(76,))

        # No longer needed because of ToMap
        # Ensures(1_000 not in self.custom__dict__)
        # Ensures(2_000 not in self.custom__dict__)
        # Ensures(900 not in self.custom__dict__)

    @Pure
    def custom__get_hidden(self, name: int) -> object:
        Requires(Acc(self.custom__dict__, 1 / 10))
        Requires(Acc(dict_pred(self.custom__dict__), 1 / 10))
        if name not in self.custom__dict__:
            return self.custom__get_attr_pure(name)
        else:
            return self.custom__dict__[name]

    @Pure
    def custom__get_attr_pure(self, name: int) -> object:
        Requires(Acc(self.custom__dict__, 1 / 10))
        Requires(Acc(dict_pred(self.custom__dict__), 1 / 10))
        if name == 1_000:
            # return self.custom__dict__[76] + 5        # mypy won't allow this
            return 15
        elif name > 1_000:
            return "abcd"
        # else:
        #     raise Exception()
        else:
            return CustomExceptionInstance

@Predicate
def Dynamic_predicate(d: Dynamic) -> bool:
    return Acc(d.custom__dict__, 1) and \
           Acc(dict_pred(d.custom__dict__), 1) and \
           (76 in d.custom__dict__ and isinstance(d.custom__dict__[76], int))


def do_something_with_attributes(d: Dynamic) -> None:
    Requires(Acc(d.custom__dict__, 1 / 10))
    Requires(Acc(dict_pred(d.custom__dict__), 1 / 10))

    Requires(isinstance(d.custom__get_hidden(76), int))
    Requires(d.custom__get_hidden(76) == 99)
    Requires(d.custom__get_hidden(1_000) == 15)
    Requires(d.custom__get_hidden(2_000) == "abcd")

    print(d.custom__get_hidden(76))
    print("== 99!")

    Ensures(Acc(d.custom__dict__, 1 / 10))
    Ensures(Acc(dict_pred(d.custom__dict__), 1 / 10))


def main() -> None:
    d = Dynamic(99)

    Fold(Dynamic_predicate(d))
    # now permission to custom__dict__ is inside Dynamic_predicate

    Unfold(Dynamic_predicate(d))
    Assert(d.custom__dict__[76] == 99)
    Assert(ToMap(d.custom__dict__).keys() == PSet(76,))
    Assert(isinstance(d.custom__get_hidden(76), int))
    Assert(d.custom__get_hidden(76) == 99)
    Fold(Dynamic_predicate(d))

    Unfold(Dynamic_predicate(d))
    Assert(1_000 not in d.custom__dict__)
    Assert(isinstance(d.custom__get_hidden(1_000), int))
    Assert(d.custom__get_hidden(1_000) == 15)
    Fold(Dynamic_predicate(d))

    Unfold(Dynamic_predicate(d))
    Assert(2_000 not in d.custom__dict__)
    Assert(isinstance(d.custom__get_hidden(2_000), str))
    Assert(d.custom__get_hidden(2_000) == "abcd")
    Fold(Dynamic_predicate(d))

    Unfold(Dynamic_predicate(d))
    Assert(900 not in d.custom__dict__)
    Assert(isinstance(d.custom__get_hidden(900), CustomException))
    do_something_with_attributes(d)
    d.custom__dict__[76] = "abcd"
    # Fold(Dynamic_predicate(d))        # the user shouldn't expect the invariant to hold if they
                                        # never fold it back up


if __name__ == "__main__":
    main()

