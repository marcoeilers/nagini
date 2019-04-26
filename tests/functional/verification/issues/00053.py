# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import (
    Exsures,
)


def callee() -> int:
    Exsures(Exception, True)
    raise Exception()


#:: ExpectedOutput(carbon)(postcondition.violated:assertion.false)
def caller() -> int:
    try:
        a = callee()
    except:
        #:: ExpectedOutput(expression.undefined:undefined.local.variable)
        return a
    return 5
