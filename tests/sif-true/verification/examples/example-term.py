# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

def main(h: int) -> None:
    old_h = h
    while h != 0:
        Invariant(Implies(old_h < 0, h < 0))
        Invariant(Implies(old_h >= 0, h >= 0))
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)|ExpectedOutput(carbon)(termination_channel_check.failed:sif_termination.not_lowevent)
        Invariant(TerminatesSif(h >= 0, h + 1))
        h = h - 1
