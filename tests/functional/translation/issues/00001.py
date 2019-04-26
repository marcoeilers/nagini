# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


#:: ExpectedOutput(type.error:Encountered Any type. Type annotation missing?)
def test1():
    raise Exception()
