# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

def m() -> None:
    a = (1,2,3,4,5,6)
    #:: ExpectedOutput(type.error:Two starred expressions in assignment)
    b, *c, *d = a