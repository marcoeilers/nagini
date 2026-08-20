# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

#:: ExpectedOutput(type.error:MarkGhost takes only Type aliases.)
MarkGhost(int)

def main(i: int) -> None:
    i += 1
