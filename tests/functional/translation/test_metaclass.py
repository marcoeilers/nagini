# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from abc import ABCMeta


class MyMeta(ABCMeta):
    pass


#:: ExpectedOutput(unsupported:Unsupported metaclass)
class A(metaclass=MyMeta):
    pass
