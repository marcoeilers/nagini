from nagini_contracts.contracts import *

def main(h: int) -> None:
    while h != 0:
        Invariant(Implies(Old(h >= 0), h >= 0))
        #:: ExpectedOutput(termination_channel_check.failed:sif_termination.condition_not_low)
        Invariant(TerminatesSif(h >= 0, h + 1))
        h = h - 1
