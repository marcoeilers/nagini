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
