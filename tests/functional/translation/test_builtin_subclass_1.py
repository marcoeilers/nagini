# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


#:: ExpectedOutput(unsupported:Subclassing builtin type is currently not supported.)
class A(str):
    pass
