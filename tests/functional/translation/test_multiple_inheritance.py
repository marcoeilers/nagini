# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class A:
    pass


class B:
    pass


#:: ExpectedOutput(unsupported:multiple inheritance)
class C(A, B):
    pass
