# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/


from nagini_contracts.contracts import *
from nagini_contracts.adt import ADT
from typing import (
    NamedTuple,
)

class Segment_ADT(ADT):
    pass


class Segment(Segment_ADT, NamedTuple('Segment', [('length', int), ('value', int)])):
    pass


@Pure
def segment_eq_lemma(s1: Segment, s2: Segment) -> bool:
    Requires(s1.length == s2.length)
    Requires(s1.value == s2.value)
    Ensures(s1 == s2)
    return True

@Pure
def segment_eq_lemma_2(s1: Segment, s2: Segment) -> bool:
    Requires(s1.length is s2.length)
    Requires(s1.value is s2.value)
    Ensures(s1 == s2)
    return True

@Pure
def segment_eq_lemma_3(s1: Segment, s2: Segment) -> bool:
    Requires(s1.length == s2.length)
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(s1 == s2)
    return True