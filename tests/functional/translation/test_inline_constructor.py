# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    #:: ExpectedOutput(unsupported:Inlining constructors is currently not supported.)
    @Inline
    def __init__(self) -> None:
        pass
