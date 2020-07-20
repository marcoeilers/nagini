# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from typing import Optional


class Cont1:
    pass


class Cont2:
    pass


OptionalCont1 = Optional[Cont1]


def return_optional_fail(b: bool) -> None:
    result = object()
    if b:
        result = None
    else:
        result = Cont2()
    #:: ExpectedOutput(type.error:Parameterized generics cannot be used with class or instance checks)|ExpectedOutput(type.error:Argument 2 to "isinstance" has incompatible type "object"; expected "Union[type; Tuple[Union[type; Tuple[Any; ...]]; ...]]")
    assert isinstance(result, OptionalCont1)