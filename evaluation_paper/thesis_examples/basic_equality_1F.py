# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


# reflexivity postcodition is violated:
# ensures self == other ==> result
class B:
    @Pure
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        return False

# modularity postcondition is violated:
# ensures result ==> type(self) == type(other) (mentioned set M_C is empty)
class C:
    @Pure
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        return True

# We do not know the exact type of self, only that it's 
# an instance of E
class E:
    @Pure
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    def __eq__(self, other: object) -> bool:
        Requires(state_pred(self))
        Requires(Implies(not Stateless(other), state_pred(other)))
        Ensures(
            Implies(type(other) == E, Result())
        )
        if type(other) == E:
            return True
        return False
    