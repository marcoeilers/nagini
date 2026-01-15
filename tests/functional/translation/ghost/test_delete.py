# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

global_var: int = 0

@Ghost
def main() -> None:
    global global_var
    #:: ExpectedOutput(invalid.program:invalid.ghost.delete)
    del global_var
