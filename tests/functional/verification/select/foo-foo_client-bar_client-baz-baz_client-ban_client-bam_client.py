# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def foo() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 6)
    return 5

def foo_client() -> int:
    Ensures(Result() == 6)
    return foo()


def bar() -> int:
    #ExpectedOutput(postcondition.violated:assertion.false)  # not selected
    Ensures(Result() == 6)
    return 5

def bar_client() -> int:
    Ensures(Result() == 6)
    return bar()

@Pure
@Opaque
def baz() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 6)
    return 5

def baz_client() -> int:
    Ensures(Result() == 6)
    return baz()


@Pure
@Opaque
def bam() -> int:
    #ExpectedOutput(postcondition.violated:assertion.false)  # not selected
    Ensures(Result() == 6)
    return 5

def bam_client() -> int:
    Ensures(Result() == 6)
    return bam()


@Pure
@Opaque
def ban() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 6)
    return 5

def ban_client() -> int:
    Ensures(Result() == 6)
    return Reveal(ban())